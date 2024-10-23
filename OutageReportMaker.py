import streamlit as st
import pandas as pd
import numpy as np

# Title for the app
st.title("Outage Data Analysis")

# Sidebar for Client Site Count option
show_client_site_count = st.sidebar.checkbox("Show Client Site Count from RMS Station Status Report")

# Load the default RMS Station Status Report
try:
    default_file_path = "RMS Station Status Report.xlsx"  
    df_default = pd.read_excel(default_file_path, header=2)
    df_default.columns = df_default.columns.str.strip()

    # Extract Clients from Site Alias
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
            reports = {}
            for client in df['Client'].unique():
                client_df = df[df['Client'] == client]
                report = generate_report(client_df, client)
                reports[client] = report

# Section for Client Site Count from RMS Station Status Report
if show_client_site_count:
    st.subheader("Client Site Count from RMS Station Status Report")

    # Load the initial file from the repository for Client Site Count
    if not regions_zones.empty:
        try:
            initial_file_path = "RMS Station Status Report.xlsx"  
            df_initial = pd.read_excel(initial_file_path, header=2)
            df_initial.columns = df_initial.columns.str.strip()

            # Process the initial file to extract client names and count by Cluster/Zone
            if 'Site Alias' in df_initial.columns:
                df_initial['Clients'] = df_initial['Site Alias'].str.findall(r'\((.*?)\)')

                # Explode the dataframe for each client found
                df_exploded = df_initial.explode('Clients')

                # Group by Client, Cluster, and Zone
                client_site_count = df_exploded.groupby(['Clients', 'Cluster', 'Zone']).size().reset_index(name='Site Count')

                # Get unique clients
                unique_clients = client_site_count['Clients'].unique()

                # Display separate tables for each client
                for client in unique_clients:
                    client_table = client_site_count[client_site_count['Clients'] == client]
                    total_count = client_table['Site Count'].sum()

                    # Add the total count at the beginning
                    st.write(f"**Client Site Count Table for {client}:**")
                    st.write(f"**Total Site Count for {client}:** {total_count}")
                    st.table(client_table)

            else:
                st.error("The required 'Site Alias' column is not found in the initial file.")
        except FileNotFoundError:
            st.error("Initial file not found.")

# Optional section: Upload a new RMS Station Status Report
st.subheader("Optional: Upload a New RMS Station Status Report")
uploaded_rms_file = st.file_uploader("Upload a new RMS Station Status Report", type="xlsx")

if uploaded_rms_file:
    df_uploaded_rms = pd.read_excel(uploaded_rms_file, header=2)
    df_uploaded_rms.columns = df_uploaded_rms.columns.str.strip()

    if 'Site Alias' in df_uploaded_rms.columns:
        df_uploaded_rms['Clients'] = df_uploaded_rms['Site Alias'].str.findall(r'\((.*?)\)')
        df_uploaded_rms_exploded = df_uploaded_rms.explode('Clients')

        # Merge with the previously generated reports
        for client in df_uploaded_rms_exploded['Clients'].unique():
            st.write(f"Updated RMS report for {client}")
            # Process similar to the initial file upload or further actions
            st.table(df_uploaded_rms_exploded[df_uploaded_rms_exploded['Clients'] == client])

# Load Previous Outage Data and Map Redeem Hours
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

                # Now map the elapsed time into the outage report table
                if selected_client in reports:
                    report = reports[selected_client]
                    report = pd.merge(report, pivot_elapsed_time, how='left', on='Zone')
                    report = report.rename(columns={'Elapsed Time (hours)': 'Total Redeem Hours'})
                    report['Total Redeem Hours'] = report['Total Redeem Hours'].fillna(0)

                    # Merging Client Site Count with Updated report
                    client_site_count_filtered = client_site_count[client_site_count['Clients'] == selected_client]
                    merged_report = pd.merge(report, client_site_count_filtered, how='outer', left_on=['Region', 'Zone'], right_on=['Cluster', 'Zone'])

                    merged_report = merged_report[['Region', 'Zone', 'Site Count', 'Duration (hours)', 'Event Count', 'Total Redeem Hours']]
                    merged_report['Total Site Count'] = merged_report['Site Count_y'].fillna(0)
                    merged_report = merged_report.drop(columns=['Site Count_y'])

                    st.write(f"Final Merged Report for {selected_client}:")
                    st.table(merged_report)
            else:
                st.error(f"No data available for the client '{selected_client}'")
        else:
            st.error("The required columns 'Elapsed Time', 'Zone', and 'Tenant' are not found.")
    else:
        st.error("The 'Report Summary' sheet is not found in the uploaded Previous Outage Data.")
