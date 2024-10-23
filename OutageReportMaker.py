import streamlit as st
import pandas as pd
import numpy as np
import io

# Title for the app
st.title("Outage Data Analysis")

# Step 1: Upload Outage Data file
uploaded_outage_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

if uploaded_outage_file:
    xl_outage = pd.ExcelFile(uploaded_outage_file)
    
    if 'RMS Alarm Elapsed Report' in xl_outage.sheet_names:
        df_outage = xl_outage.parse('RMS Alarm Elapsed Report', header=2)
        df_outage.columns = df_outage.columns.str.strip()

        if 'Site Alias' in df_outage.columns:
            # Extract client and site name
            df_outage['Client'] = df_outage['Site Alias'].str.extract(r'\((.*?)\)')
            df_outage['Site Name'] = df_outage['Site Alias'].str.extract(r'^(.*?)\s*\(')

            # Process timestamps and calculate duration
            df_outage['Start Time'] = pd.to_datetime(df_outage['Start Time'], errors='coerce')
            df_outage['End Time'] = pd.to_datetime(df_outage['End Time'], errors='coerce')
            df_outage['Duration (hours)'] = (df_outage['End Time'] - df_outage['Start Time']).dt.total_seconds() / 3600
            df_outage['Duration (hours)'] = df_outage['Duration (hours)'].apply(lambda x: round(x, 2) if pd.notnull(x) else 0)

            st.success("Outage data uploaded and processed.")
        else:
            st.error("The required 'Site Alias' column is not found in the Outage data.")
    else:
        st.error("The 'RMS Alarm Elapsed Report' sheet is not found in the Outage data.")

# Step 2: Upload Previous Outage Data file
uploaded_previous_file = st.file_uploader("Please upload a Previous Outage Excel Data file", type="xlsx")

if uploaded_outage_file and uploaded_previous_file:
    xl_previous = pd.ExcelFile(uploaded_previous_file)
    
    if 'Report Summary' in xl_previous.sheet_names:
        df_previous = xl_previous.parse('Report Summary', header=2)
        df_previous.columns = df_previous.columns.str.strip()

        if 'Elapsed Time' in df_previous.columns and 'Zone' in df_previous.columns and 'Tenant' in df_previous.columns:
            
            # Convert elapsed time to hours
            def convert_to_hours(elapsed_time):
                try:
                    total_seconds = pd.to_timedelta(elapsed_time).total_seconds()
                    return round(total_seconds / 3600, 2)
                except:
                    return 0

            df_previous['Elapsed Time (hours)'] = df_previous['Elapsed Time'].apply(convert_to_hours)

            # Map tenant names
            tenant_map = {
                'Grameenphone': 'GP', 'Banglalink': 'BL', 'Robi': 'ROBI', 'Banjo': 'BANJO'
            }
            df_previous['Tenant'] = df_previous['Tenant'].replace(tenant_map)

            # Step 3: Merge outage data and previous outage data
            clients = df_outage['Client'].unique()
            reports = {}

            for client in clients:
                client_outage_df = df_outage[df_outage['Client'] == client]

                # Aggregate outage data
                client_agg = client_outage_df.groupby(['Cluster', 'Zone']).agg(
                    Site_Count=('Site Alias', 'nunique'),
                    Duration=('Duration (hours)', 'sum'),
                    Event_Count=('Site Alias', 'count')
                ).reset_index()

                # Filter previous outage data for the client
                client_previous_df = df_previous[df_previous['Tenant'] == client]
                pivot_elapsed_time = client_previous_df.pivot_table(index='Zone', values='Elapsed Time (hours)', aggfunc='sum').reset_index()

                # Merge both datasets
                report = pd.merge(client_agg, pivot_elapsed_time, how='left', on='Zone')
                report['Elapsed Time (hours)'] = report['Elapsed Time (hours)'].fillna(0)
                report = report.rename(columns={'Elapsed Time (hours)': 'Total Redeem Hours'})

                # Add total row
                total_row = pd.DataFrame({
                    'Cluster': ['Total'],
                    'Zone': [''],
                    'Site_Count': [report['Site_Count'].sum()],
                    'Duration (hours)': [report['Duration (hours)'].sum()],
                    'Event_Count': [report['Event_Count'].sum()],
                    'Total Redeem Hours': [report['Total Redeem Hours'].sum()]
                })
                report = pd.concat([report, total_row], ignore_index=True)

                reports[client] = report

            # Step 4: Display the merged table with the custom header
            report_date = st.date_input("Select Outage Report Date", value=pd.to_datetime("today"))
            for client, report in reports.items():
                st.markdown(
                    f'<h4>SC wise <b>{client}</b> Site Outage Status on <b>{report_date}</b> '
                    f'<i><small>(as per RMS)</small></i></h4>',
                    unsafe_allow_html=True
                )
                st.table(report[['Cluster', 'Zone', 'Site_Count', 'Duration (hours)', 'Event_Count', 'Total Redeem Hours']])

        else:
            st.error("The required columns 'Elapsed Time', 'Zone', and 'Tenant' are not found in the Previous Outage data.")
    else:
        st.error("The 'Report Summary' sheet is not found in the Previous Outage data.")
