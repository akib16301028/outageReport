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

            # Function to generate the outage report
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

            # Generate reports for each client
            clients = np.append('All', df['Client'].unique())
            reports = {}
            for client in df['Client'].unique():
                client_df = df[df['Client'] == client]
                report = generate_report(client_df, client)
                reports[client] = report

# Section for Client Site Count from RMS Station Status Report
if show_client_site_count:
    st.subheader("Client Site Count from RMS Station Status Report")

    # Load the initial file for Client Site Count
    if not regions_zones.empty:
        try:
            initial_file_path = "RMS Station Status Report.xlsx"  # The initial file in your GitHub repo
            df_initial = pd.read_excel(initial_file_path, header=2)
            df_initial.columns = df_initial.columns.str.strip()

            # Process the initial file to extract client names and count by Cluster/Zone
            if 'Site Alias' in df_initial.columns:
                df_initial['Clients'] = df_initial['Site Alias'].str.findall(r'\((.*?)\)')
                df_exploded = df_initial.explode('Clients')

                # Group by Client, Cluster, and Zone
                client_site_count = df_exploded.groupby(['Clients', 'Cluster', 'Zone']).size().reset_index(name='Site Count')

                # Get unique clients
                unique_clients = client_site_count['Clients'].unique()

                # Display separate tables for each client
                for client in unique_clients:
                    client_table = client_site_count[client_site_count['Clients'] == client]
                    total_count = client_table['Site Count'].sum()
                    st.write(f"Client Site Count Table for {client}:")
                    st.write(f"**Total for {client}:** {total_count}")

                    st.table(client_table)

                # Optional Upload: New RMS Station Status Report
                st.subheader("Optional: Upload a New RMS Station Status Report")
                new_rms_file = st.file_uploader("Upload New RMS Station Status Report", type="xlsx")

                if new_rms_file:
                    df_new_rms = pd.read_excel(new_rms_file, header=2)
                    df_new_rms.columns = df_new_rms.columns.str.strip()
                    st.write("New RMS Station Status Report Uploaded")

            else:
                st.error("The required 'Site Alias' column is not found in the initial file.")
        except FileNotFoundError:
            st.error("Initial file not found.")

# Merging Client Site Count with the Outage Report
if show_client_site_count and uploaded_outage_file:
    if not reports:
        st.error("No outage data is available.")
    else:
        for client in reports:
            report = reports[client]
            client_site_count_for_client = client_site_count[client_site_count['Clients'] == client]

            # Add Total Site Count column
            report['Total Site Count'] = 0

            # Merge the tables
            for idx, site_row in client_site_count_for_client.iterrows():
                cluster = site_row['Cluster']
                zone = site_row['Zone']
                site_count = site_row['Site Count']

                # Match the region and zone in the report
                match = (report['Region'] == cluster) & (report['Zone'] == zone)

                if match.any():
                    # If match is found, update the Total Site Count
                    report.loc[match, 'Total Site Count'] = site_count
                else:
                    # Append new row if Region and Zone is not found in report
                    new_row = {
                        'Region': cluster,
                        'Zone': zone,
                        'Total Site Count': site_count,
                        'Site Count': 0,
                        'Duration (hours)': 0,
                        'Event Count': 0,
                        'Total Redeem Hours': 0
                    }
                    report = report.append(new_row, ignore_index=True)

            st.write(f"Updated Report for Client: {client}")
            st.table(report)
