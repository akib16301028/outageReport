import streamlit as st
import pandas as pd
import numpy as np
import io

# Other parts of your code...

# Function to display the table
def display_table(client_name, report, report_date):
    st.markdown(
        f'<h4>SC wise <b>{client_name}</b> Site Outage Status on <b>{report_date}</b> '
        f'<i><small>(as per RMS)</small></i></h4>', 
        unsafe_allow_html=True
    )
    report['Duration (hours)'] = report['Duration (hours)'].apply(lambda x: f"{x:.2f}")
    st.table(report)

# Function to generate the report
def generate_report(client_df, regions_zones):
    full_report = regions_zones.copy()
    client_agg = client_df.groupby(['Cluster', 'Zone']).agg(
        Site_Count=('Site Alias', 'nunique'),
        Duration=('Duration (hours)', 'sum'),
        Event_Count=('Site Alias', 'count')
    ).reset_index()

    # Merge with the full report
    report = pd.merge(full_report, client_agg, how='left', on=['Cluster', 'Zone'])
    report = report.fillna(0)  # Fill NaNs with zeros
    report['Duration'] = report['Duration'].apply(lambda x: round(x, 2))  # Rounding the duration

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
        'Site Count': [report['Site Count'].sum()],
        'Duration (hours)': [report['Duration (hours)'].sum()],
        'Event Count': [report['Event Count'].sum()]
    })
    report = pd.concat([report, total_row], ignore_index=True)

    return report

# Within your main report generation logic
if st.session_state.generate_report:
    client_df = df[df['Client'] == selected_client]
    
    if not client_df.empty:  # Check if client_df has data
        report = generate_report(client_df, regions_zones)
        if not report.empty:  # Check if report is not empty
            display_table(selected_client, report, report_date)
        else:
            st.warning("No outage data found for the selected client.")
    else:
        st.warning("No data available for the selected client.")
