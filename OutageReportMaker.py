import streamlit as st
import pandas as pd
import numpy as np
import io

# Step 1: Upload file for Outage Data
st.title("Outage Data Analysis")

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

                def generate_report(client_df):
                    report = client_df.groupby(['Cluster', 'Zone']).agg(
                        Site_Count=('Site Alias', 'nunique'),
                        Duration=('Duration (hours)', 'sum'),
                        Event_Count=('Site Alias', 'count')
                    ).reset_index()
                    report = report.rename(columns={
                        'Cluster': 'Region',
                        'Site_Count': 'Site Count',
                        'Event_Count': 'Event Count',
                        'Duration': 'Duration (hours)'
                    })
                    total_row = pd.DataFrame({
                        'Region': ['Total'],
                        'Zone': [''],
                        'Site Count': [report['Site Count'].sum()],
                        'Duration (hours)': [report['Duration (hours)'].sum()],
                        'Event Count': [report['Event Count'].sum()]
                    })
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

# Section 2: Upload RMS Site List
st.subheader("Upload RMS Station Status Report")

uploaded_site_list_file = st.file_uploader("Please upload RMS Station Status Report", type="xlsx")

if uploaded_site_list_file:
    xl_site_list = pd.ExcelFile(uploaded_site_list_file)
    df_site_list = xl_site_list.parse(header=2)
    df_site_list.columns = df_site_list.columns.str.strip()

    if 'Site Alias' in df_site_list.columns:
        df_site_list['Client'] = df_site_list['Site Alias'].str.extract(r'\((.*?)\)')
        
        def generate_client_report(df):
            client_report = df.groupby(['Client', 'Cluster', 'Zone']).agg(Site_Count=('Site Alias', 'nunique')).reset_index()
            return client_report
        
        client_report = generate_client_report(df_site_list)
        
        st.write("Client-wise Site Count Report")
        st.table(client_report)
        
        # Function to update and download
        def to_excel_site_list(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Client Count Report', index=False)
            output.seek(0)
            return output
        
        if st.button("Download Client Count Report"):
            output_site_list = to_excel_site_list(client_report)
            st.download_button(label="Download Excel", data=output_site_list, file_name="Client_Count_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("The required 'Site Alias' column is not found.")
else:
    st.warning("Please upload a valid RMS Station Status Report.")
