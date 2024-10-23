import streamlit as st
import pandas as pd
import numpy as np
import io

# Title for the app
st.title("Outage Data Analysis")

# Sidebar options
st.sidebar.header("Options")
show_site_count = st.sidebar.checkbox("Show Client Site Count from RMS Station Status Report")

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
                st.write(f"Showing data for Client: {selected_client}")
                pivot_elapsed_time = df_filtered.pivot_table(index='Zone', values='Elapsed Time (hours)', aggfunc='sum').reset_index()
                total_row = pd.DataFrame({'Zone': ['Total'], 'Elapsed Time (hours)': [pivot_elapsed_time['Elapsed Time (hours)'].sum()]})
                pivot_elapsed_time = pd.concat([pivot_elapsed_time, total_row], ignore_index=True)
                pivot_elapsed_time['Elapsed Time (hours)'] = pivot_elapsed_time['Elapsed Time (hours)'].apply(lambda x: f"{x:.2f}")
                st.write("Pivot Table for Elapsed Time by Zone (Filtered by Client)")
                st.table(pivot_elapsed_time)

                # Now map the elapsed time into the outage report table
                if selected_client in reports:
                    report = reports[selected_client]
                    report = pd.merge(report, pivot_elapsed_time, how='left', on='Zone')
                    report = report.rename(columns={'Elapsed Time (hours)': 'Total Redeem Hours'})
                    report['Total Redeem Hours'] = report['Total Redeem Hours'].fillna(0)
                    st.write(f"Updated report for {selected_client} with Total Redeem Hours:")
                    st.table(report)
            else:
                st.error(f"No data available for the client '{selected_client}'")
        else:
            st.error("The required columns 'Elapsed Time', 'Zone', and 'Tenant' are not found.")
    else:
        st.error("The 'Report Summary' sheet is not found.")

# Upload Outage Data
st.subheader("Upload Outage Data")
uploaded_outage_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

if uploaded_outage_file and not regions_zones.empty:
    report_date = st.date_input("Select Outage Report Date", value=pd.to_datetime("today"))

    if 'generate_report' not in st.session_state:
        st.session_state.generate_report = False

    if st.button("Generate Report"):
        st.session_state.generate_report = True
    
    if st.session_state.generate_report:
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
                    report['Duration (hours)'] = report['Duration (hours)'].apply(lambda x: round(x, 2))

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

                selected_client = st.selectbox("Select a client to filter", options=clients, index=0)

                def display_table(client_name, report):
                    st.markdown(
                        f'<h4>SC wise <b>{client_name}</b> Site Outage Status on <b>{report_date}</b> '
                        f'<i><small>(as per RMS)</small></i></h4>', 
                        unsafe_allow_html=True
                    )
                    report['Duration (hours)'] = report['Duration (hours)'].apply(lambda x: f"{x:.2f}")
                    st.table(report)
                    return report

                if selected_client == 'All':
                    for client in df['Client'].unique():
                        report = reports[client]
                        display_table(client, report)
                else:
                    report = reports[selected_client]
                    display_table(selected_client, report)

                # Function to convert to excel
                def to_excel():
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, sheet_name='Original Data', index=False)
                        for client, report in reports.items():
                            report.to_excel(writer, sheet_name=f'{client} Report', index=False)
                    output.seek(0)
                    return output

                if st.button("Download Report"):
                    output = to_excel()
                    file_name = f"SC wise {selected_client} Site Outage Status on {report_date}.xlsx"
                    st.download_button(label="Download Excel Report", data=output, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.success("Report generated and ready to download!")
            else:
                st.error("The required 'Site Alias' column is not found.")

# Section for Client Site Count from RMS Station Status Report
if show_site_count and not regions_zones.empty:
    st.subheader("Client Site Count from RMS Station Status Report")

    # Load the initial file from the repository for Client Site Count
    try:
        initial_file_path = "RMS Station Status Report.xlsx"  # The initial file in your GitHub repo
        df_initial = pd.read_excel(initial_file_path, header=2)
        df_initial.columns = df_initial.columns.str.strip()

        # Process the initial file to extract client names and count by Cluster/Zone
        if 'Site Alias' in df_initial.columns:
            df_initial['Clients'] = df_initial['Site Alias'].str.findall(r'\((.*?)\)')

            # Explode the dataframe for each client found
            df_exploded = df_initial.explode('Clients')

            # Group by Client, Cluster, and Zone
            client_site_count = df_exploded.groupby(['Clients', 'Cluster', 'Zone']).size().reset_index(name='Site Count')

            # Option to update the Client Site Count
            if st.button("Update Client Site Count"):
                # Reprocess the data
                updated_client_site_count = df_exploded.groupby(['Clients', 'Cluster', 'Zone']).size().reset_index(name='Site Count')
                st.success("Client Site Count updated!")
                st.table(updated_client_site_count)

            st.write("Client Site Count Table:")
            st.table(client_site_count)
        else:
            st.error("The required 'Site Alias' column is not found in the initial file.")
    except FileNotFoundError:
        st.error("Initial file not found.")
