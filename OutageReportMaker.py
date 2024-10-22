import streamlit as st
import pandas as pd
import numpy as np
import io

# Step 1: Upload Outage Data file
st.title("Outage Data Analysis")
uploaded_file = st.file_uploader("Please upload an Outage Excel Data file", type="xlsx")

# Step 2: Date input with a calendar, initially disabled until file is uploaded
if uploaded_file:
    report_date = st.date_input("Select Outage Report Date", value=pd.to_datetime("today"))

    # Step 3: Generate button to show reports only after clicking it
    if 'generate_report' not in st.session_state:
        st.session_state.generate_report = False

    if st.button("Generate Report"):
        st.session_state.generate_report = True  # Set the flag to indicate report generation

    if st.session_state.generate_report:  # Only proceed if the button has been clicked
        
        # Load the Excel file and specific sheet with header at row 3 (index 2)
        xl = pd.ExcelFile(uploaded_file)
        if 'RMS Alarm Elapsed Report' in xl.sheet_names:
            # Read the sheet with header at the third row
            df = xl.parse('RMS Alarm Elapsed Report', header=2)

            # Remove leading/trailing spaces in case column names have spaces
            df.columns = df.columns.str.strip()

            if 'Site Alias' in df.columns:
                # Extract client from Site Alias column
                df['Client'] = df['Site Alias'].str.extract(r'\((.*?)\)')
                df['Site Name'] = df['Site Alias'].str.extract(r'^(.*?)\s*\(')

                # Modify the time columns to calculate duration
                df['Start Time'] = pd.to_datetime(df['Start Time'])
                df['End Time'] = pd.to_datetime(df['End Time'])
                df['Duration (hours)'] = (df['End Time'] - df['Start Time']).dt.total_seconds() / 3600

                # Round the Duration to 2 decimal places with rounding logic
                df['Duration (hours)'] = df['Duration (hours)'].apply(lambda x: round(x, 2) if x >= 0.01 else np.nan)

                # Function to generate a report for each client
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

                # Generate a table for each client
                reports = {}
                for client in df['Client'].unique():
                    client_df = df[df['Client'] == client]
                    report = generate_report(client_df)
                    reports[client] = report

                # Client Filter panel with 'All' option
                clients = np.append('All', df['Client'].unique())  # Add 'All' option
                selected_client = st.selectbox("Select a client to filter", options=clients, index=0)

                # Option to show site count tables
                show_tables = st.checkbox("Show Site Count Tables", value=False)

                # Function to display the table for the selected client
                def display_table(client_name, report):
                    # Smaller and formatted text for the header
                    st.markdown(
                        f'<h4>SC wise <b>{client_name}</b> Site Outage Status on <b>{report_date}</b> '
                        f'<i><small>(as per RMS)</small></i></h4>', 
                        unsafe_allow_html=True
                    )

                    # Format 'Duration (hours)' to show two decimal places
                    report['Duration (hours)'] = report['Duration (hours)'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

                    # Show the table with formatted data
                    st.table(report)

                # Display either all tables or the filtered table based on selection
                if selected_client == 'All':
                    if show_tables:
                        for client in df['Client'].unique():
                            report = reports[client]
                            display_table(client, report)
                    else:
                        st.write("Select 'Show Site Count Tables' to view the tables for each client.")
                else:
                    if show_tables:
                        report = reports[selected_client]
                        display_table(selected_client, report)
                    else:
                        st.write("Select 'Show Site Count Tables' to view the table for the selected client.")

                # Function to convert DataFrame to Excel file
                def to_excel():
                    # Create a BytesIO buffer for the Excel file
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        # Write original data to the first sheet
                        df.to_excel(writer, sheet_name='Original Data', index=False)

                        # Write outage report to a new sheet
                        for client, report in reports.items():
                            report.to_excel(writer, sheet_name=f'{client} Report', index=False)
                    output.seek(0)
                    return output

                # Prepare the download button for the final report
                if st.button("Download Report"):
                    output = to_excel()
                    file_name = f"SC wise {selected_client} Site Outage Status on {report_date}.xlsx"
                    st.download_button(label="Download Excel Report", data=output, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    st.success("Report generated and ready to download!")

            else:
                st.error("The required 'Site Alias' column is not found.")
else:
    st.warning("Please upload a valid Excel file.")
