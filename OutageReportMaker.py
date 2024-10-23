import streamlit as st
import pandas as pd

# Title for the app
st.title("Outage Data Analysis")

# Initialize session state for the update button
if 'update_triggered' not in st.session_state:
    st.session_state['update_triggered'] = False

# Sidebar for uploading Power Availability data
uploaded_power_file = st.sidebar.file_uploader("Please upload Power Availability Data (Excel file)", type="xlsx")

# Initialize DataFrames
availability_df = pd.DataFrame()
average_availability = pd.DataFrame()

# Process the uploaded Power Availability data
if uploaded_power_file:
    xl_power = pd.ExcelFile(uploaded_power_file)
    if 'Site wise summary' in xl_power.sheet_names:
        availability_df = xl_power.parse('Site wise summary', header=0)
        availability_df.columns = availability_df.columns.str.strip()  # Clean column names

        # Check if required columns exist
        required_columns = ['Zone', 'AC Availability (%)', 'DC Availability (%)']
        if all(col in availability_df.columns for col in required_columns):
            # Calculate average AC and DC availability by Zone
            average_availability = availability_df.groupby('Zone').agg(
                Avg_AC_Availability=('AC Availability (%)', 'mean'),
                Avg_DC_Availability=('DC Availability (%)', 'mean')
            ).reset_index()
            average_availability['Avg_AC_Availability'] = average_availability['Avg_AC_Availability'].round(2)
            average_availability['Avg_DC_Availability'] = average_availability['Avg_DC_Availability'].round(2)
        else:
            st.error("The required columns are not found in the uploaded file.")
    else:
        st.error("The 'Site wise summary' sheet is not found in the uploaded file.")

# Display average availability table
if not average_availability.empty:
    st.subheader("Average Power Availability by Zone")
    st.table(average_availability)

# Upload Outage Data
uploaded_outage_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

if uploaded_outage_file:
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
                relevant_regions_zones = average_availability[['Zone']].drop_duplicates()
                full_report = relevant_regions_zones.copy()

                # Grouping by Cluster and Zone to aggregate required metrics
                client_agg = client_df.groupby(['Cluster', 'Zone']).agg(
                    Site_Count=('Site Alias', 'nunique'),
                    Duration=('Duration (hours)', 'sum'),
                    Event_Count=('Site Alias', 'count')
                ).reset_index()

                # Merge with average availability data
                report = pd.merge(full_report, client_agg, how='left', left_on=['Zone'], right_on=['Zone'])
                report = pd.merge(report, average_availability, how='left', on='Zone')
                report = report.fillna(0)

                # Rename columns
                report = report.rename(columns={
                    'Cluster': 'Region',
                    'Site_Count': 'Site Count',
                    'Event_Count': 'Event Count',
                    'Duration': 'Duration (hours)'
                })
                reports[client] = report

            # Display the reports for clients
            selected_client = st.selectbox("Select a Client (Tenant)", list(reports.keys()) + ["All"])

            if selected_client == "All":
                # Display combined report for all clients
                combined_report = pd.concat(reports.values())
                st.write("Combined Report for All Clients:")
                st.table(combined_report)
            elif selected_client in reports:
                st.write(f"Merged Report for {selected_client}:")
                st.table(reports[selected_client])

# Option to add AC and DC availability to Merged Report
if not average_availability.empty:
    if st.sidebar.checkbox("Add AC and DC Availability to Merged Report"):
        st.subheader("Merged Report with AC and DC Availability")
        if 'Zone' in combined_report.columns:
            # Merge average availability data into the combined report
            combined_report_with_availability = pd.merge(combined_report, average_availability, how='left', on='Zone')
            st.table(combined_report_with_availability)
