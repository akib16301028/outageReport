import streamlit as st
import pandas as pd
import numpy as np

# Step 1: Ask for the outage report date
report_date = st.text_input("Outage Report for the Date?", value="YYYY-MM-DD")

# Step 2: Upload file
st.title("Outage Data Analysis App")
uploaded_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

if uploaded_file:
    # Step 3: Load the Excel file and specific sheet with header at row 3 (index 2)
    xl = pd.ExcelFile(uploaded_file)
    if 'RMS Alarm Elapsed Report' in xl.sheet_names:
        # Read the sheet with header at the third row
        df = xl.parse('RMS Alarm Elapsed Report', header=2)

        # Remove leading/trailing spaces in case column names have spaces
        df.columns = df.columns.str.strip()

        if 'Site Alias' in df.columns:
            # Step 4: Extract client from Site Alias column
            df['Client'] = df['Site Alias'].str.extract(r'\((.*?)\)')
            df['Site Name'] = df['Site Alias'].str.extract(r'^(.*?)\s*\(')

            # Step 5: Modify the time columns to calculate duration
            df['Start Time'] = pd.to_datetime(df['Start Time'])
            df['End Time'] = pd.to_datetime(df['End Time'])
            df['Duration (hours)'] = (df['End Time'] - df['Start Time']).dt.total_seconds() / 3600

            # Round the Duration to 2 decimal places
            df['Duration (hours)'] = df['Duration (hours)'].round(2)

            # Step 6: Aggregate the data and rename the columns
            def generate_report(client_df):
                report = client_df.groupby(['Cluster', 'Zone']).agg(
                    Site_Count=('Site Alias', 'nunique'),
                    Duration=('Duration (hours)', 'sum'),
                    Event_Count=('Site Alias', 'count')
                ).reset_index()

                # Rename columns as per the requirements
                report = report.rename(columns={
                    'Cluster': 'Region',
                    'Site_Count': 'Site Count',
                    'Event_Count': 'Event Count',
                    'Duration': 'Duration (hours)'
                })

                # Calculate total row
                total_row = pd.DataFrame({
                    'Region': ['Total'],
                    'Zone': [''],
                    'Site Count': [report['Site Count'].sum()],
                    'Duration (hours)': [report['Duration (hours)'].sum()],
                    'Event Count': [report['Event Count'].sum()]
                })
                report = pd.concat([report, total_row], ignore_index=True)

                return report

            # Step 7: Generate table for each client
            clients = df['Client'].unique()
            reports = {}
            for client in clients:
                client_df = df[df['Client'] == client]
                report = generate_report(client_df)
                reports[client] = report

            # Step 8: Add filtering option at the top
            selected_client = st.selectbox("Select a client to filter", options=clients)

            if selected_client:
                st.write(f"### **SC wise {selected_client} Site Outage Status on {report_date}** *(_as per RMS_)**")
                
                report = reports[selected_client]

                # Step 9: Display the table with merged Region cells
                def merge_region_cells(report):
                    # We will use pandas' style to format the table and merge cells for the same Region
                    report_style = report.style.set_properties(subset=['Region'], **{'text-align': 'center'}) \
                                                .format({'Duration (hours)': "{:.2f}"})

                    # Hide duplicate Region names (simulate merged cells effect)
                    report['Region'] = report['Region'].mask(report['Region'].duplicated(), '')

                    return report, report_style

                merged_report, styled_report = merge_region_cells(report)

                # Display the merged and formatted table
                st.table(merged_report)

            # Step 10: Add download option for the final report
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
