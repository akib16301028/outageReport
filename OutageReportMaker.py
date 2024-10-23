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

# Upload Previous Outage Data
st.subheader("Upload Previous Outage Data")
uploaded_previous_file = st.file_uploader("Please upload a Previous Outage Excel Data file", type="xlsx", key="previous_outage_file")

# Upload Outage Data
st.subheader("Upload Outage Data")
uploaded_outage_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx", key="outage_file")

# Initialize session state for reports if not present
if 'reports' not in st.session_state:
    st.session_state.reports = {}
if 'previous_data' not in st.session_state:
    st.session_state.previous_data = None

# Generate Report Button
if uploaded_previous_file and uploaded_outage_file:
    if st.button("Generate Report"):
        # Process Previous Outage Data
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

                # Store the previous data in session state
                st.session_state.previous_data = df_previous
            else:
                st.error("The required columns 'Elapsed Time', 'Zone', and 'Tenant' are not found.")
                st.session_state.previous_data = None
        else:
            st.error("The 'Report Summary' sheet is not found.")
            st.session_state.previous_data = None

        # Process Current Outage Data
        xl = pd.ExcelFile(uploaded_outage_file)
        if 'RMS Alarm Elapsed Report' in xl.sheet_names:
            df = xl.parse('RMS Alarm Elapsed Report', header=2)
            df.columns = df.columns.str.strip()

            if 'Site Alias' in df.columns:
                df['Client'] = df['Site Alias'].str.extract(r'\((.*?)\)')
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
                for client in df['Client'].unique():
                    client_df = df[df['Client'] == client]
                    report = generate_report(client_df, client)
                    st.session_state.reports[client] = report

                # Display the merged report
                selected_client = st.selectbox("Select a client to filter", options=clients, index=0)

                def display_table(client_name, report):
                    st.markdown(
                        f'<h4>SC wise <b>{client_name}</b> Site Outage Status</h4>', 
                        unsafe_allow_html=True
                    )
                    report['Duration (hours)'] = report['Duration (hours)'].apply(lambda x: f"{x:.2f}")
                    return report

                if selected_client == 'All':
                    for client in df['Client'].unique():
                        report = st.session_state.reports[client]
                        display_table(client, report)
                else:
                    report = st.session_state.reports[selected_client]
                    display_table(selected_client, report)

                # Function to convert to excel
                def to_excel():
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, sheet_name='Original Data', index=False)
                        for client, report in st.session_state.reports.items():
                            report.to_excel(writer, sheet_name=f'{client} Report', index=False)
                    output.seek(0)
                    return output

                if st.button("Download Report"):
                    output = to_excel()
                    file_name = f"Outage Report_{selected_client}.xlsx"
                    st.download_button(label="Download Excel Report", data=output, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.success("Report generated and ready to download!")
            else:
                st.error("The required 'Site Alias' column is not found.")
else:
    st.info("Please upload both Previous Outage Data and Current Outage Data files to generate the report.")

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

            st.write("Client Site Count Table:")
            st.table(client_site_count)
        else:
            st.error("The required 'Site Alias' column is not found in the initial file.")
    except FileNotFoundError:
        st.error("Initial file not found.")
