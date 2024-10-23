import streamlit as st
import pandas as pd
import numpy as np

# Title for the app
st.title("Outage Data Analysis")

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

# Upload Outage Data
uploaded_outage_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

reports = {}
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

            # Function to generate the report
            def generate_report(client_df, selected_client):
                relevant_zones = df_default[df_default['Site Alias'].str.contains(selected_client)]
                if relevant_zones.empty:
                    return pd.DataFrame(columns=['Region', 'Zone', 'Site Count', 'Duration (hours)', 'Event Count'])

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

                return report

            clients = np.append('All', df['Client'].unique())

            for client in df['Client'].unique():
                client_df = df[df['Client'] == client]
                report = generate_report(client_df, client)
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
            
            def convert_to_hours(elapsed_time):
                try:
                    total_seconds = pd.to_timedelta(elapsed_time).total_seconds()
                    hours = total_seconds / 3600
                    return round(hours, 2)
                except:
                    return 0

            df_previous['Elapsed Time (hours)'] = df_previous['Elapsed Time'].apply(convert_to_hours)
            tenant_map = {
                'Grameenphone': 'GP', 'Banglalink': 'BL', 'Robi': 'ROBI', 'Banjo': 'BANJO'
            }

            df_previous['Tenant'] = df_previous['Tenant'].replace(tenant_map)

            clients = df_previous['Tenant'].unique()
            selected_client = st.selectbox("Select a Client (Tenant)", clients)

            df_filtered = df_previous[df_previous['Tenant'] == selected_client]

            if not df_filtered.empty:
                pivot_elapsed_time = df_filtered.pivot_table(index='Zone', values='Elapsed Time (hours)', aggfunc='sum').reset_index()
                pivot_elapsed_time['Elapsed Time (hours)'] = pivot_elapsed_time['Elapsed Time (hours)'].apply(lambda x: f"{x:.2f}")

                # Map the elapsed time into the outage report table
                if selected_client in reports:
                    report = reports[selected_client]
                    report = pd.merge(report, pivot_elapsed_time, how='left', on='Zone')
                    report = report.rename(columns={'Elapsed Time (hours)': 'Total Redeem Hours'})
                    report['Total Redeem Hours'] = report['Total Redeem Hours'].fillna(0)

                    # Merging the client site count with the current report
                    client_site_count = df_default_exploded.groupby(['Clients', 'Cluster', 'Zone']).size().reset_index(name='Site Count')

                    # Display Merged Report for Client
                    merged_report = pd.merge(report, client_site_count, how='left', left_on=['Region', 'Zone'], right_on=['Cluster', 'Zone'])
                    merged_report = merged_report.drop(columns=['Cluster', 'Clients'])
                    merged_report = merged_report.fillna(0)
                    merged_report = merged_report.rename(columns={'Site Count_x': 'Site Count', 'Site Count_y': 'Total Site Count'})
                    merged_report['Total Site Count'] = merged_report['Total Site Count'].astype(int)

                    st.write(f"Merged Report for {selected_client}:")
                    st.table(merged_report)
                    
            else:
                st.error(f"No data available for the client '{selected_client}'")
        else:
            st.error("The required columns 'Elapsed Time', 'Zone', and 'Tenant' are not found.")
    else:
        st.error("The 'Report Summary' sheet is not found.")

# Sidebar Options
with st.sidebar:
    show_client_site_count = st.checkbox("Show Client Site Count from RMS Station Status Report", value=True)
    show_update_button = st.checkbox("Optional: Upload a New RMS Station Status Report")

# Optional: Add a button for updating client-wise site status
if st.sidebar.button("Update Client Site Status"):
    st.sidebar.write("Client site status updated based on the uploaded file.")
