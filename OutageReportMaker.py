import streamlit as st
import pandas as pd
import numpy as np
import io

# Title for the app
st.title("Outage Data Analysis")

# Step 1: Load the default RMS Station Status Report file
try:
    default_file_path = "RMS Station Status Report.xlsx"  # Default file path
    df_default = pd.read_excel(default_file_path, header=2)
    df_default.columns = df_default.columns.str.strip()

    # Extract Regions and Zones from the default file
    if 'Site Alias' in df_default.columns:
        df_default['Clients'] = df_default['Site Alias'].str.findall(r'\((.*?)\)')
        df_default_exploded = df_default.explode('Clients')
        regions_zones = df_default_exploded[['Cluster', 'Zone']].drop_duplicates().reset_index(drop=True)
    else:
        st.error("The required 'Site Alias' column is not found in the default file.")
        regions_zones = pd.DataFrame()  # Empty DataFrame to avoid errors

except FileNotFoundError:
    st.error("Default file not found.")
    regions_zones = pd.DataFrame()  # Empty DataFrame to avoid errors

# Step 2: Upload file for Outage Data
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

                def generate_report(client_df, client_name):
                    # Create a full report structure with all regions and zones
                    full_report = regions_zones.copy()
                    client_agg = client_df.groupby(['Cluster', 'Zone']).agg(
                        Site_Count=('Site Alias', 'nunique'),
                        Duration=('Duration (hours)', 'sum'),
                        Event_Count=('Site Alias', 'count')
                    ).reset_index()

                    # Calculate Total Site Count for the selected client
                    total_site_count = client_agg['Site_Count'].sum()

                    # Merge the client aggregated report with the full report
                    report = pd.merge(full_report, client_agg, how='left', on=['Cluster', 'Zone'])
                    report = report.fillna(0)  # Fill NaNs with zeros

                    # Add additional columns
                    report['Total Site Count'] = total_site_count
                    report['Total Hours'] = report['Total Site Count'] * 24 * 30
                    report['Affected Site Count'] = report['Site_Count']
                    report['Outage Duration'] = report['Duration']
                    report['Total Allowable Limit (Hour)'] = report['Total Hours'] - (report['Total Hours'] * 0.9985)

                    # Rename columns
                    report = report.rename(columns={
                        'Cluster': 'Region',
                        'Site_Count': 'Site Count',
                        'Event_Count': 'Event Count',
                        'Duration': 'Duration (hours)'
                    })

                    # Add total row
                    total_row = pd.DataFrame({
                        'Region': ['Total'],
                        'Zone': [''],
                        'Total Site Count': [report['Total Site Count'].sum()],
                        'Total Hours': [report['Total Hours'].sum()],
                        'Affected Site Count': [report['Affected Site Count'].sum()],
                        'Outage Duration': [report['Outage Duration'].sum()],
                        'Event Count': [report['Event Count'].sum()],
                        'Total Allowable Limit (Hour)': [report['Total Allowable Limit (Hour)'].sum()]
                    })
                    report = pd.concat([report, total_row], ignore_index=True)
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
                    report['Outage Duration'] = report['Outage Duration'].apply(lambda x: f"{x:.2f}")
                    st.table(report)
                    return report

                if selected_client == 'All':
                    for client in df['Client'].unique():
                        report = reports[client]
                        display_table(client, report)
                else:
                    report = reports[selected_client]
                    display_table(selected_client, report)

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
else:
    if uploaded_outage_file:
        st.warning("Regions and zones not available from the default file. Please ensure it is uploaded.")
    else:
        st.warning("Please upload a valid Outage Excel file.")

# Section 2: RMS Site List Processing with Multiple Clients

st.subheader("Client Site Count from RMS Station Status Report")

# Load the initial file from GitHub repository
if not regions_zones.empty:
    try:
        initial_file_path = "RMS Station Status Report.xlsx"  # The initial file in your GitHub repo
        df_initial = pd.read_excel(initial_file_path, header=2)
        df_initial.columns = df_initial.columns.str.strip()

        # Process the initial file to extract client names and count by Cluster/Zone
        if 'Site Alias' in df_initial.columns:
            df_initial['Clients'] = df_initial['Site Alias'].str.findall(r'\((.*?)\)')

            # Explode the dataframe for each client found
            df_exploded = df_initial.explode('Clients')

            # Group by Client, Cluster, and Zone to count site occurrences
            client_report_initial = df_exploded.groupby(['Clients', 'Cluster', 'Zone']).agg(Site_Count=('Site Alias', 'nunique')).reset_index()

            # Show the initial processed data
            st.write("Initial Client Site Count Report (from repository)")
            st.table(client_report_initial)
        else:
            st.error("The required 'Site Alias' column is not found in the initial repository file.")

    except FileNotFoundError:
        st.error("Initial file not found in repository.")

# Step 2: Allow user to upload a new file to update
uploaded_site_list_file = st.file_uploader("Upload new RMS Station Status Report to update", type="xlsx")

if uploaded_site_list_file:
    df_uploaded = pd.read_excel(uploaded_site_list_file, header=2)
    df_uploaded.columns = df_uploaded.columns.str.strip()

    if 'Site Alias' in df_uploaded.columns:
        # Extract multiple clients from the 'Site Alias' column
        df_uploaded['Clients'] = df_uploaded['Site Alias'].str.findall(r'\((.*?)\)')

        # Explode the dataframe for each client found
        df_uploaded_exploded = df_uploaded.explode('Clients')

        # Group by Client, Cluster, and Zone to count site occurrences
        client_report_uploaded = df_uploaded_exploded.groupby(['Clients', 'Cluster', 'Zone']).agg(Site_Count=('Site Alias', 'nunique')).reset_index()

        # Show the updated data
        st.write("Updated Client Site Count Report")
        st.table(client_report_uploaded)

        # Function to convert updated report to Excel and download
        def to_excel_updated(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Updated Client Count', index=False)
            output.seek(0)
            return output

        if st.button("Download Updated Report"):
            output = to_excel_updated(client_report_uploaded)
            st.download_button(label="Download Updated Client Report", data=output, file_name="Updated_Client_Site_Count_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.warning("Please upload a new RMS Station Status Report to update client counts.")
