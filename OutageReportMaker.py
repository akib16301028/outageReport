import streamlit as st
import pandas as pd

# Step 1: Upload RMS Site List
st.title("RMS Site List Client Analysis")

# Upload the Excel file
uploaded_file = st.file_uploader("Please upload the RMS Site List file", type="xlsx")

if uploaded_file:
    # Load the Excel file and process 'RMS Station Status Report' from row 3
    df = pd.read_excel(uploaded_file, sheet_name='RMS Station Status Report', header=2)
    
    # Ensure there's no leading/trailing space in column names
    df.columns = df.columns.str.strip()

    # Extract client names from 'Site Alias'
    df['Clients'] = df['Site Alias'].str.findall(r'\((.*?)\)')
    df = df.explode('Clients')

    # Group by Client, Cluster, Zone and count the number of sites
    def generate_client_report():
        client_reports = {}
        for client in df['Clients'].unique():
            client_df = df[df['Clients'] == client]
            report = client_df.groupby(['Cluster', 'Zone']).agg(
                Site_Count=('Site', 'nunique')
            ).reset_index()

            # Adding a Total row for each client
            total_row = pd.DataFrame({
                'Cluster': ['Total'],
                'Zone': [''],
                'Site_Count': [report['Site_Count'].sum()]
            })
            report = pd.concat([report, total_row], ignore_index=True)
            client_reports[client] = report

        return client_reports

    # Generate client reports
    client_reports = generate_client_report()

    # Step 2: Checkbox to show/hide Site Count tables
    show_site_count = st.checkbox("Show Site Count Tables")

    if show_site_count:
        for client, report in client_reports.items():
            st.markdown(f"### {client}")
            st.table(report)
