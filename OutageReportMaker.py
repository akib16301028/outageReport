import streamlit as st
import pandas as pd
import numpy as np

# Title for the app
st.title("Outage Data Analysis")

# Initialize session state for the update button
if 'update_triggered' not in st.session_state:
    st.session_state['update_triggered'] = False

# Sidebar for Client Site Count option and Update button
show_client_site_count = st.sidebar.checkbox("Show Client Site Count from RMS Station Status Report")
kpi_filter = st.sidebar.selectbox("Select Site Type", ["All", "KPI", "Non-KPI"])
client_filter = st.sidebar.selectbox("Select Client", ["All"])  # Placeholder for client filter

# Button for updating site count
if st.sidebar.button("Update"):
    st.session_state['update_triggered'] = True

# Load the default RMS Station Status Report
try:
    default_file_path = "RMS Station Status Report.xlsx"
    df_default = pd.read_excel(default_file_path, header=2)
    df_default.columns = df_default.columns.str.strip()
    if 'Site Alias' in df_default.columns:
        df_default['Clients'] = df_default['Site Alias'].str.findall(r'\((.*?)\)')
        df_default_exploded = df_default.explode('Clients')
        regions_zones = df_default_exploded[['Cluster', 'Zone']].drop_duplicates().reset_index(drop=True)
    else:
        st.error("The required 'Site Alias' column is not found in the default file.")
        regions_zones = pd.DataFrame()
except FileNotFoundError:
    st.error("Default file not found.")
    regions_zones = pd.DataFrame()

# Upload Power Availability Data
uploaded_power_file = st.sidebar.file_uploader("Please upload Power Availability Data (Excel file)", type="xlsx")

# Initialize DataFrames for average availability
availability_df = pd.DataFrame()
average_availability = pd.DataFrame()

# Process the uploaded Power Availability data
if uploaded_power_file:
    xl_power = pd.ExcelFile(uploaded_power_file)
    if 'Site wise summary' in xl_power.sheet_names:
        availability_df = xl_power.parse('Site wise summary', header=2)
        availability_df.columns = availability_df.columns.str.strip()  # Clean column names

        # Check if required columns exist
        required_columns = ['Zone', 'AC Availability (%)', 'DC Availability (%)']
        if all(col in availability_df.columns for col in required_columns):
            # Calculate average AC and DC availability by Zone, ignoring non-KPI sites
            filtered_availability = availability_df[~availability_df['Site'].str.startswith('L')]
            average_availability = filtered_availability.groupby('Zone').agg(
                Avg_AC_Availability=('AC Availability (%)', 'mean'),
                Avg_DC_Availability=('DC Availability (%)', 'mean')
            ).reset_index()
            average_availability['Avg_AC_Availability'] = average_availability['Avg_AC_Availability'].round(2)
            average_availability['Avg_DC_Availability'] = average_availability['Avg_DC_Availability'].round(2)
        else:
            st.error("The required columns are not found in the uploaded Power Availability file.")
    else:
        st.error("The 'Site wise summary' sheet is not found in the uploaded Power Availability file.")

# Upload Outage Data
uploaded_outage_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

if uploaded_outage_file and not regions_zones.empty:
    xl = pd.ExcelFile(uploaded_outage_file)
    if 'RMS Alarm Elapsed Report' in xl.sheet_names:
        df = xl.parse('RMS Alarm Elapsed Report', header=2)
        df.columns = df.columns.str.strip()

        if 'Site Alias' in df.columns:
            df['Client'] = df['Site Alias'].str.extract(r'\((.*?)\)')
            df['Site Name'] = df['Site Alias'].str.extract(r'^(.*?)\s*\(')
            df['Start Time'] = pd.to_datetime(df['Start Time'])
            df['End Time'] = pd.to_datetime(df['End Time'])
            df['Duration (hours)'] = (df['End Time'] - df['Start Time']).dt.total_seconds() / 3600
            df['Duration (hours)'] = df['Duration (hours)'].apply(lambda x: round(x, 2))

            # Generate client reports
            reports = {}
            for client in df['Client'].unique():
                client_df = df[df['Client'] == client]
                relevant_zones = df_default[df_default['Site Alias'].str.contains(client)]
                relevant_regions_zones = relevant_zones[['Cluster', 'Zone']].drop_duplicates()
                full_report = relevant_regions_zones.copy()
                client_agg = client_df.groupby(['Cluster', 'Zone']).agg(
                    Site_Count=('Site Alias', 'nunique'),
                    Duration=('Duration (hours)', 'sum'),
                    Event_Count=('Site Alias', 'count')
                ).reset_index()
                report = pd.merge(full_report, client_agg, how='left', left_on=['Cluster', 'Zone'], right_on=['Cluster', 'Zone'])
                report = report.fillna(0)
                report['Duration'] = report['Duration'].apply(lambda x: round(x, 2))
                report = report.rename(columns={
                    'Cluster': 'Region',
                    'Site_Count': 'Site Count',
                    'Event_Count': 'Event Count',
                    'Duration': 'Duration (hours)'
                })
                reports[client] = report

# Upload Previous Outage Data and Map Redeem Hours
st.subheader("Upload Previous Outage Data")

uploaded_previous_file = st.file_uploader("Please upload a Previous Outage Excel Data file", type="xlsx")

if uploaded_previous_file:
    xl_previous = pd.ExcelFile(uploaded_previous_file)
    
    if 'Report Summary' in xl_previous.sheet_names:
        df_previous = xl_previous.parse('Report Summary', header=2)
        df_previous.columns = df_previous.columns.str.strip()

        if 'Elapsed Time' in df_previous.columns and 'Zone' in df_previous.columns and 'Tenant' in df_previous.columns:
            
            # Convert elapsed time to hours
            def convert_to_hours(elapsed_time):
                try:
                    total_seconds = pd.to_timedelta(elapsed_time).total_seconds()
                    hours = total_seconds / 3600
                    return round(hours, 2)
                except:
                    return 0

            df_previous['Elapsed Time (hours)'] = df_previous['Elapsed Time'].apply(convert_to_hours)
            tenant_map = {'Grameenphone': 'GP', 'Banglalink': 'BL', 'Robi': 'ROBI', 'Banjo': 'BANJO'}
            df_previous['Tenant'] = df_previous['Tenant'].replace(tenant_map)

            clients = df_previous['Tenant'].unique()
            client_filter = st.selectbox("Select a Client (Tenant)", ["All"] + clients.tolist())

            df_filtered = df_previous
            if client_filter != "All":
                df_filtered = df_previous[df_previous['Tenant'] == client_filter]

            if not df_filtered.empty:
                # Pivot table to get total redeemed hours per zone
                pivot_elapsed_time = df_filtered.pivot_table(index='Zone', values='Elapsed Time (hours)', aggfunc='sum').reset_index()
                pivot_elapsed_time['Elapsed Time (hours)'] = pivot_elapsed_time['Elapsed Time (hours)'].apply(lambda x: f"{x:.2f}")

                # Merge the reports with the previous redeemed hours
                if client_filter in reports:
                    report = reports[client_filter] if client_filter != "All" else pd.concat(reports.values())
                    report = pd.merge(report, pivot_elapsed_time, how='left', on='Zone')
                    report = report.rename(columns={'Elapsed Time (hours)': 'Total Redeem Hours'})
                    report['Total Redeem Hours'] = report['Total Redeem Hours'].fillna(0)

                    # Merge with Client Site Count
                    client_site_count = df_default_exploded.groupby(['Clients', 'Cluster', 'Zone']).size().reset_index(name='Site Count')
                    client_table = client_site_count.copy()

                    # Apply KPI/non-KPI filter
                    if kpi_filter == "KPI":
                        client_table = client_table[~client_table['Clients'].str.startswith('L')]
                    elif kpi_filter == "Non-KPI":
                        client_table = client_table[client_table['Clients'].str.startswith('L')]

                    if client_filter != "All":
                        client_table = client_table[client_table['Clients'] == client_filter]

                    merged_report = pd.merge(report, client_table, how='left', left_on=['Region', 'Zone'], right_on=['Cluster', 'Zone'])
                    merged_report = merged_report.drop(columns=['Cluster', 'Clients'])
                    merged_report = merged_report.fillna(0)
                    merged_report['Total Site Count'] = merged_report['Site Count_y'].fillna(0).astype(int)

                    # Display the final merged report
                    st.write(f"Merged Report for {client_filter}:")
                    st.table(merged_report)
            else:
                st.error(f"No data available for the client '{client_filter}'")
        else:
            st.error("The required columns 'Elapsed Time', 'Zone', and 'Tenant' are not found.")
    else:
        st.error("The 'Report Summary' sheet is not found.")

# Sidebar option to show client-wise site table
if show_client_site_count or st.session_state['update_triggered']:
    st.subheader("Client Site Counts")
    
    # Create a summary table based on the selected filters
    if 'Clients' in df_default_exploded.columns:
        # Count the total sites by client
        client_site_count = df_default_exploded.groupby(['Clients', 'Cluster', 'Zone']).size().reset_index(name='Site Count')
        
        # Apply KPI/non-KPI filter
        if kpi_filter == "KPI":
            client_site_count = client_site_count[~client_site_count['Clients'].str.startswith('L')]
        elif kpi_filter == "Non-KPI":
            client_site_count = client_site_count[client_site_count['Clients'].str.startswith('L')]

        # Further filter by client if selected
        if client_filter != "All":
            client_site_count = client_site_count[client_site_count['Clients'] == client_filter]

        # If 'All' clients are selected, summarize by zone
        if client_filter == "All":
            client_site_count_summary = client_site_count.groupby(['Cluster', 'Zone']).agg(Total_Site_Count=('Site Count', 'sum')).reset_index()
            st.write("Total Site Count by Zone:")
            st.table(client_site_count_summary)
        else:
            st.write(f"Client-wise Site Count for {client_filter}:")
            st.table(client_site_count)
    else:
        st.error("No client data available to display site counts.")

# Reset update trigger after displaying the table
if st.session_state['update_triggered']:
    st.session_state['update_triggered'] = False

# Display the average availability if data has been processed
if not average_availability.empty:
    st.subheader("Average Availability by Zone")
    st.table(average_availability)

# Provide feedback to the user
st.sidebar.markdown("### Notes:")
st.sidebar.markdown("""
- Make sure to upload the necessary files for data processing.
- Use the filters to customize the view of the site counts and reports.
""")
