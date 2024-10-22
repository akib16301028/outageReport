import streamlit as st
import pandas as pd
import numpy as np
import io

# Title for the app
st.title("Outage Data Analysis")

# Step 1: Upload file for Outage Data
uploaded_outage_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

if uploaded_outage_file:
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

                # Get unique regions and zones from the data
                regions = df['Cluster'].unique()
                zones = df['Zone'].unique()

                # Function to generate report for each client
                def generate_report(client_df):
                    report = pd.DataFrame(columns=['Region', 'Zone', 'Site Count', 'Duration (hours)', 'Event Count'])
                    
                    for region in regions:
                        for zone in zones:
                            # Filter for the current region and zone
                            site_count = client_df[(client_df['Cluster'] == region) & (client_df['Zone'] == zone)]['Site Alias'].nunique()
                            duration = client_df[(client_df['Cluster'] == region) & (client_df['Zone'] == zone)]['Duration (hours)'].sum()
                            event_count = client_df[(client_df['Cluster'] == region) & (client_df['Zone'] == zone)]['Site Alias'].count()
                            
                            # Create a new row
                            new_row = {
                                'Region': region,
                                'Zone': zone,
                                'Site Count': site_count,
                                'Duration (hours)': duration if duration else 0,
                                'Event Count': event_count
                            }
                            # Append the new row to the report DataFrame
                            report = pd.concat([report, pd.DataFrame([new_row])], ignore_index=True)

                    # Calculate total row
                    total_row = report.sum(numeric_only=True).to_frame().T
                    total_row['Region'] = 'Total'
                    total_row['Zone'] = ''
                    report = pd.concat([report, total_row], ignore_index=True)

                    return report

                clients = np.append('All', df['Client'].unique())
                reports = {}
                for client in df['Client'].unique():
                    client_df = df[df['Client'] == client]
                    report = generate_report(client_df)
                    reports[client] = report

                selected_client = st.selectbox("Select a client to filter", options=clients, index=0)

                def display_table(client_name, report):
                    st.markdown(
                        f'<h4>SC wise <b>{client_name}</b> Site Outage Status on <b>{report_date}</b> '
                        f'<i><small>(as per RMS)</small></i></h4>', 
                        unsafe_allow_html=True
                    )
                    report['Duration (hours)'] = report['Duration (hours)'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "0.00")
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
    st.warning("Please upload a valid Outage Excel file.")


# Section 2: RMS Site List Processing with Multiple Clients

st.subheader("Client Site Count from RMS Station Status Report")

# Step 1: Load the initial file from GitHub repository
try:
    initial_file_path = "RMS Station Status Report.xlsx"  # The initial file in your GitHub repo
    df_initial = pd.read_excel(initial_file_path, header=2)
    df_initial.columns = df_initial.columns.str.strip()

    # Process the initial file to extract client names and count by Cluster/Zone
    if 'Site Alias' in df_initial.columns:
        # Extract multiple clients from the 'Site Alias' column
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
                df.to_excel(writer, sheet_name='Client Count Report', index=False)
            output.seek(0)
            return output

        if st.button("Download Updated Client Count Report"):
            output_uploaded = to_excel_updated(client_report_uploaded)
            st.download_button(label="Download Excel", data=output_uploaded, file_name="Updated_Client_Count_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    else:
        st.error("The required 'Site Alias' column is not found.")
