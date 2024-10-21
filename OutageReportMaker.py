import streamlit as st
import pandas as pd
import numpy as np

# Step 1: Upload file
st.title("Outage Data Analysis App")
uploaded_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

# Step 2: Date input with a calendar
if uploaded_file:
    report_date = st.date_input("Select Outage Report Date", value=pd.to_datetime("today"))

    # Generate button to show reports only after clicking it
    if st.button("Generate Report"):
        
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
                clients = np.append('All', df['Client'].unique())  # Add 'All' option
                reports = {}
                for client in df['Client'].unique():
                    client_df = df[df['Client'] == client]
                    report = generate_report(client_df)
                    reports[client] = report

                # Step 8: Client Filter panel with 'All' option
                selected_client = st.selectbox("Select a client to filter", options=clients, index=0)

                # Step 9: Display either all tables or filtered table based on selection
                def display_table(client_name, report):
                    # Smaller and formatted text for the header
                    st.markdown(
                        f'<h4>SC wise <b>{client_name}</b> Site Outage Status on <b>{report_date}</b> '
                        f'<i><small>(as per RMS)</small></i></h4>', 
                        unsafe_allow_html=True
                    )

                    # Show table with formatted columns and total row
                    st.table(report)

                if selected_client == 'All':
                    for client in df['Client'].unique():
                        report = reports[client]
                        display_table(client, report)
                else:
                    report = reports[selected_client]
                    display_table(selected_client, report)

                # Step 10: Add download option for the final report
                def to_excel():
                    with pd.ExcelWriter("outage_report.xlsx", engine='xlsxwriter') as writer:
                        # Write original data to the first sheet
                        df.to_excel(writer, sheet_name='Original Data', index=False)

                        # Write outage report to a new sheet
                        for client, report in reports.items():
                            report.to_excel(writer, sheet_name=f'{client} Report', index=False)

                if st.button("Download Report"):
                    to_excel()
                    st.success("Report generated and ready to download!")
            else:
                st.error("The required 'Site Alias' column is not found.")
else:
    st.warning("Please upload a valid Excel file.")
