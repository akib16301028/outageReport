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
    if 'Site Wise Summary' in xl_power.sheet_names:
        availability_df = xl_power.parse('Site Wise Summary', header=2)
        availability_df.columns = availability_df.columns.str.strip()  # Clean column names

        # Check if required columns exist
        required_columns = ['Zone', 'AC Availability (%)', 'DC Availability (%)']
        if all(col in availability_df.columns for col in required_columns):
            # Calculate exact average AC and DC availability by Zone, ignoring KPI designation
            average_availability = availability_df.groupby('Zone').agg(
                Avg_AC_Availability=('AC Availability (%)', 'mean'),
                Avg_DC_Availability=('DC Availability (%)', 'mean')
            ).reset_index()
            average_availability['Avg_AC_Availability'] = average_availability['Avg_AC_Availability'].round(2)
            average_availability['Avg_DC_Availability'] = average_availability['Avg_DC_Availability'].round(2)
        else:
            st.error("The required columns are not found in the uploaded Power Availability file.")
    else:
        st.error("The 'Site Wise Summary' sheet is not found in the uploaded Power Availability file.")

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

# Sidebar option to show client-wise site table
if show_client_site_count or st.session_state['update_triggered']:  # Trigger client-site count update with button click
    st.subheader("Client Site Count from RMS Station Status Report")

    # Add a filter for client names
    client_filter_option = st.sidebar.selectbox(
        "Select a Client to view Site Count",
        options=["All"] + list(df_default_exploded['Clients'].unique())
    )

    # Checkbox for including both KPI and non-KPI sites
    show_non_kpi = st.sidebar.checkbox("Show Non-KPI Sites (Sites starting with 'L')", value=False)

    if not regions_zones.empty:
        client_site_count = df_default_exploded.groupby(['Clients', 'Cluster', 'Zone']).size().reset_index(name='Site Count')

        # Filter client site count based on selection
        if client_filter_option != "All":
            client_site_count = client_site_count[client_site_count['Clients'] == client_filter_option]

        # Exclude non-KPI sites by default
        if not show_non_kpi:
            client_site_count = client_site_count[~client_site_count['Cluster'].str.startswith('L')]

        unique_clients = client_site_count['Clients'].unique()

        # Display the site count table
        for client in unique_clients:
            client_table = client_site_count[client_site_count['Clients'] == client]
            total_row = pd.DataFrame(client_table.sum(numeric_only=True)).T
            total_row['Cluster'] = 'Total'
            client_table = pd.concat([client_table, total_row], ignore_index=True).drop_duplicates(keep='last')

            st.write(f"Client Site Count for {client}")
            st.table(client_table)
    else:
        st.error("No site data available.")
