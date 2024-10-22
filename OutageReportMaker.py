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

                # Step 3: Upload Previous Outage Data File
                uploaded_previous_file = st.file_uploader("Please upload a Previous Outage Excel Data file", type="xlsx", key="prev")

                total_redeem_hours = {}

                if uploaded_previous_file:
                    xl_previous = pd.ExcelFile(uploaded_previous_file)
                    
                    if 'Report Summary' in xl_previous.sheet_names:
                        df_previous = xl_previous.parse('Report Summary', header=2)  # Header starts from row 3 (index 2)
                        df_previous.columns = df_previous.columns.str.strip()
                        
                        if 'Elapsed Time' in df_previous.columns and 'Zone' in df_previous.columns and 'Tenant' in df_previous.columns:
                            
                            # Convert Elapsed Time to hours
                            df_previous['Elapsed Time (hours)'] = df_previous['Elapsed Time'].apply(lambda x: x.total_seconds() / 3600 if isinstance(x, pd.Timedelta) else 0)

                            # Creating a mapping for total redeem hours by zone and client
                            for index, row in df_previous.iterrows():
                                tenant_name = row['Tenant'].strip().title()
                                zone_name = row['Zone'].strip()
                                hours = row['Elapsed Time (hours)']
                                
                                # Normalizing client name
                                client_name_mapping = {
                                    "Grameenphone": "GP",
                                    "Banglalink": "BL",
                                    "Robi": "ROBI",
                                    "Banjo": "BANJO"
                                }
                                
                                client_name = client_name_mapping.get(tenant_name, tenant_name)
                                
                                if client_name not in total_redeem_hours:
                                    total_redeem_hours[client_name] = {}
                                if zone_name not in total_redeem_hours[client_name]:
                                    total_redeem_hours[client_name][zone_name] = 0
                                total_redeem_hours[client_name][zone_name] += hours
                        else:
                            st.error("The required columns 'Elapsed Time', 'Zone', and 'Tenant' are not found.")
                    else:
                        st.error("The 'Report Summary' sheet is not found.")

                def generate_report(client_df, selected_client):
                    # Extract regions and zones relevant to the selected client
                    relevant_zones = df_default[df_default['Site Alias'].str.contains(selected_client)]
                    if relevant_zones.empty:
                        return pd.DataFrame(columns=['Region', 'Zone', 'Site Count', 'Duration (hours)', 'Event Count', 'Total Redeem Hours'])

                    relevant_regions_zones = relevant_zones[['Cluster', 'Zone']].drop_duplicates()

                    # Create a full report structure with the relevant regions and zones
                    full_report = relevant_regions_zones.copy()
                    client_agg = client_df.groupby(['Cluster', 'Zone']).agg(
                        Site_Count=('Site Alias', 'nunique'),
                        Duration=('Duration (hours)', 'sum'),
                        Event_Count=('Site Alias', 'count')
                    ).reset_index()

                    # Merge the client aggregated report with the full report
                    report = pd.merge(full_report, client_agg, how='left', left_on=['Cluster', 'Zone'], right_on=['Cluster', 'Zone'])
                    report = report.fillna(0)  # Fill NaNs with zeros
                    report['Duration'] = report['Duration'].apply(lambda x: round(x, 2))  # Rounding the duration

                    # Rename columns
                    report = report.rename(columns={
                        'Cluster': 'Region',
                        'Site_Count': 'Site Count',
                        'Event_Count': 'Event Count',
                        'Duration': 'Duration (hours)'
                    })

                    # Add Total Redeem Hours
                    for index, row in report.iterrows():
                        client_name = selected_client if selected_client != 'All' else row['Region']  # Adjust as per your logic
                        zone_name = row['Zone']
                        
                        if client_name not in total_redeem_hours:
                            st.warning(f"Client '{client_name}' not found in total redeem hours.")
                            report.at[index, 'Total Redeem Hours'] = 0
                            continue
                        
                        if zone_name not in total_redeem_hours[client_name]:
                            st.warning(f"Zone '{zone_name}' not found for client '{client_name}'.")
                            report.at[index, 'Total Redeem Hours'] = 0
                            continue
                        
                        redeem_hours = total_redeem_hours[client_name][zone_name]
                        report.at[index, 'Total Redeem Hours'] = redeem_hours

                    # Add total row
                    total_row = pd.DataFrame({
                        'Region': ['Total'],
                        'Zone': [''],
                        'Site Count': [report['Site Count'].sum()],
                        'Duration (hours)': [report['Duration (hours)'].sum()],
                        'Event Count': [report['Event Count'].sum()],
                        'Total Redeem Hours': [report['Total Redeem Hours'].sum()]
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
                    st.success("Report generated and ready for download.")
            else:
                st.error("The required 'Site Alias' column is not found in the Outage Data file.")
        else:
            st.error("The 'RMS Alarm Elapsed Report' sheet is not found.")
else:
    st.info("Upload an outage data file to proceed.")
