import streamlit as st
import pandas as pd
import numpy as np

# Title for the app
st.title("Outage Data Analysis")

# Sidebar for uploading Power Availability data
uploaded_power_file = st.sidebar.file_uploader("Please upload Power Availability data (Excel)", type="xlsx")

# Initialize variables for AC/DC availability
ac_dc_availability_df = pd.DataFrame()
if uploaded_power_file:
    # Load the Power Availability data
    xl_power = pd.ExcelFile(uploaded_power_file)
    
    # Check if the 'Site wise summary' sheet exists
    if 'Site wise summary' in xl_power.sheet_names:
        df_power = xl_power.parse('Site wise summary', header=0)
        df_power.columns = df_power.columns.str.strip()
        
        # Check if required columns are present
        required_columns = ['Rms Station', 'Site', 'Site Alias', 'Zone', 'Cluster', 'Tenant Name', 'AC Availability (%)', 'DC Availability (%)']
        if all(col in df_power.columns for col in required_columns):
            # Calculate average AC and DC availability by Zone
            ac_dc_availability_df = df_power.groupby('Zone').agg(
                AC_Average=('AC Availability (%)', 'mean'),
                DC_Average=('DC Availability (%)', 'mean')
            ).reset_index()
        else:
            st.error("Required columns are missing from the Power Availability data.")
    else:
        st.error("The 'Site wise summary' sheet is not found.")

# Upload Outage Data
uploaded_outage_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

if uploaded_outage_file:
    xl_outage = pd.ExcelFile(uploaded_outage_file)
    
    if 'RMS Alarm Elapsed Report' in xl_outage.sheet_names:
        df_outage = xl_outage.parse('RMS Alarm Elapsed Report', header=2)
        df_outage.columns = df_outage.columns.str.strip()

        if 'Site Alias' in df_outage.columns:
            df_outage['Client'] = df_outage['Site Alias'].str.extract(r'\((.*?)\)')
            df_outage['Site Name'] = df_outage['Site Alias'].str.extract(r'^(.*?)\s*\(')
            df_outage['Start Time'] = pd.to_datetime(df_outage['Start Time'])
            df_outage['End Time'] = pd.to_datetime(df_outage['End Time'])
            df_outage['Duration (hours)'] = (df_outage['End Time'] - df_outage['Start Time']).dt.total_seconds() / 3600
            df_outage['Duration (hours)'] = df_outage['Duration (hours)'].apply(lambda x: round(x, 2))

            # Generate client reports
            reports = {}
            for client in df_outage['Client'].unique():
                client_df = df_outage[df_outage['Client'] == client]
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

# Allow users to add AC/DC availability to merged report for client table
if not ac_dc_availability_df.empty:
    st.subheader("Add AC/DC Availability to Merged Report")
    selected_client = st.selectbox("Select a Client (Tenant)", reports.keys())
    if selected_client:
        report = reports[selected_client]
        # Merge AC/DC availability data
        merged_report = pd.merge(report, ac_dc_availability_df, how='left', on='Zone')
        st.write(f"Merged Report for {selected_client}:")
        st.table(merged_report)

