import streamlit as st
import pandas as pd
import numpy as np

# Title and session state initialization
st.title("Outage Data Analysis")
if 'update_triggered' not in st.session_state:
    st.session_state['update_triggered'] = False

# Sidebar controls
show_client_site_count = st.sidebar.checkbox("Show Client Site Count from RMS Station Status Report")
if st.sidebar.button("Update"):
    st.session_state['update_triggered'] = True

# Load RMS Station Status Report and extract regions and zones
try:
    df_default = pd.read_excel("RMS Station Status Report.xlsx", header=2).apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    if 'Site Alias' in df_default.columns:
        df_default['Clients'] = df_default['Site Alias'].str.findall(r'\((.*?)\)')
        df_default_exploded = df_default.explode('Clients')
        regions_zones = df_default_exploded[['Cluster', 'Zone']].drop_duplicates().reset_index(drop=True)
    else:
        st.error("The required 'Site Alias' column is missing.")
except FileNotFoundError:
    st.error("Default file not found.")
    regions_zones = pd.DataFrame()

# Upload and process Power Availability Data
uploaded_power_file = st.sidebar.file_uploader("Upload Power Availability Data (Excel file)", type="xlsx")
if uploaded_power_file:
    xl_power = pd.ExcelFile(uploaded_power_file)
    if 'Site Wise Summary' in xl_power.sheet_names:
        availability_df = xl_power.parse('Site Wise Summary', header=2).apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        if set(['Zone', 'AC Availability (%)', 'DC Availability (%)', 'Site']).issubset(availability_df.columns):
            average_availability = availability_df.groupby('Zone').agg(
                Avg_AC_Availability=('AC Availability (%)', 'mean'),
                Avg_DC_Availability=('DC Availability (%)', 'mean')
            ).reset_index().round(2)
        else:
            st.error("Required columns are missing in Power Availability file.")
    else:
        st.error("'Site Wise Summary' sheet not found in Power Availability file.")

# Upload Outage Data and calculate client-specific reports
uploaded_outage_file = st.file_uploader("Upload Outage Data file", type="xlsx")
if uploaded_outage_file and not regions_zones.empty:
    xl = pd.ExcelFile(uploaded_outage_file)
    if 'RMS Alarm Elapsed Report' in xl.sheet_names:
        df = xl.parse('RMS Alarm Elapsed Report', header=2).apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df['Client'] = df['Site Alias'].str.extract(r'\((.*?)\)')
        df['Duration (hours)'] = (pd.to_datetime(df['End Time']) - pd.to_datetime(df['Start Time'])).dt.total_seconds() / 3600

        # Generate reports for each client
        reports = {}
        for client in df['Client'].unique():
            client_df = df[df['Client'] == client]
            client_agg = client_df.groupby(['Cluster', 'Zone']).agg(
                Site_Count=('Site Alias', 'nunique'),
                Duration=('Duration (hours)', 'sum'),
                Event_Count=('Site Alias', 'count')
            ).reset_index().rename(columns={'Cluster': 'Region', 'Duration': 'Duration (hours)'})
            reports[client] = client_agg

# Upload and process Previous Outage Data
uploaded_previous_file = st.file_uploader("Upload Previous Outage Data file", type="xlsx")
if uploaded_previous_file:
    xl_previous = pd.ExcelFile(uploaded_previous_file)
    if 'Report Summary' in xl_previous.sheet_names:
        df_previous = xl_previous.parse('Report Summary', header=2).apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df_previous['Elapsed Time (hours)'] = pd.to_timedelta(df_previous['Elapsed Time']).dt.total_seconds() / 3600

        selected_client = st.selectbox("Select Client", df_previous['Tenant'].unique())
        if selected_client in reports:
            report = reports[selected_client]
            pivot_elapsed_time = df_previous[df_previous['Tenant'] == selected_client].pivot_table(index='Zone', values='Elapsed Time (hours)', aggfunc='sum').reset_index()
            report = report.merge(pivot_elapsed_time, on='Zone', how='left').rename(columns={'Elapsed Time (hours)': 'Total Redeem Hours'})
            if not average_availability.empty:
                report = report.merge(average_availability, on='Zone', how='left')
            st.write(f"Merged Report for {selected_client}:")
            st.table(report)

# Display Client Site Count from RMS Station Status Report
if show_client_site_count or st.session_state['update_triggered']:
    st.subheader("Client Site Count from RMS Station Status Report")
    unique_clients = ["All"] + df_default_exploded['Clients'].dropna().unique().tolist()
    selected_client = st.selectbox("Select a Client", unique_clients)

    if selected_client == "All":
        for client in unique_clients[1:]:
            client_table = df_default_exploded[df_default_exploded['Clients'] == client].groupby(['Cluster', 'Zone']).size().reset_index(name='Site Count')
            st.write(f"Client Site Count for {client}")
            st.table(client_table)
    else:
        client_table = df_default_exploded[df_default_exploded['Clients'] == selected_client].groupby(['Cluster', 'Zone']).size().reset_index(name='Site Count')
        st.write(f"Client Site Count for {selected_client}")
        st.table(client_table)
