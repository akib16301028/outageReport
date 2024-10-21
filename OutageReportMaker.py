import streamlit as st
import pandas as pd
import numpy as np

# Step 1: Upload file
st.title("Outage Data Analysis App")
uploaded_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

if uploaded_file:
    # Step 2: Load the Excel file and specific sheet with header at row 3 (index 2)
    xl = pd.ExcelFile(uploaded_file)
    if 'RMS Alarm Elapsed Report' in xl.sheet_names:
        # Read the sheet with header at the third row
        df = xl.parse('RMS Alarm Elapsed Report', header=2)
        
        # Step 3: Check if 'Site Alias' column exists
        st.write("Column names:", df.columns)
        
        if 'Site Alias' in df.columns:
            # Remove leading/trailing spaces in case column names have spaces
            df.columns = df.columns.str.strip()

            # Extract client name and site name from 'Site Alias' column
            df['Client'] = df['Site Alias'].str.extract(r'\((.*?)\)')
            df['Site Name'] = df['Site Alias'].str.extract(r'^(.*?)\s*\(')

            # Step 4: Modify the time columns to calculate duration
            df['Start Time'] = pd.to_datetime(df['Start Time'])
            df['End Time'] = pd.to_datetime(df['End Time'])
            df['Duration (hours)'] = (df['End Time'] - df['Start Time']).dt.total_seconds() / 3600

            # Step 5: Aggregate the data
            def generate_report(client_df):
                report = client_df.groupby(['Cluster', 'Zone']).agg(
                    Site_Count=('Site Alias', 'nunique'),
                    Duration=('Duration (hours)', 'sum'),
                    Event_Count=('Site Alias', 'count')
                ).reset_index()
                return report

            # Step 6: Generate table for each client
            clients = df['Client'].unique()
            reports = {}
            for client in clients:
                client_df = df[df['Client'] == client]
                report = generate_report(client_df)
                reports[client] = report
                st.write(f"Report for Client: {client}")
                st.table(report)

            # Step 7: Add filtering option
            selected_client = st.selectbox("Select a client to filter", options=clients)
            if selected_client:
                st.write(f"Filtered Report for Client: {selected_client}")
                st.table(reports[selected_client])

            # Step 8: Add download option for the final report
            def to_excel():
                with pd.ExcelWriter("outage_report.xlsx", engine='xlsxwriter') as writer:
                    # Write original data to the first sheet
                    df.to_excel(writer, sheet_name='Original Data', index=False)

                    # Write outage report to a new sheet
                    for client, report in reports.items():
                        report.to_excel(writer, sheet_name=f'{client} Report', index=False)

                    # Add formatting for borders
                    workbook = writer.book
                    worksheet = writer.sheets['Original Data']
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value)

            if st.button("Download Report"):
                to_excel()
                st.success("Report generated and ready to download!")
        else:
            st.error("The required 'Site Alias' column is not found.")
else:
    st.warning("Please upload a valid Excel file.")
