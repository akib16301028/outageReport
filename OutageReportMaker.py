import streamlit as st
import pandas as pd
import numpy as np

# Define the mapping for tenants
tenant_mapping = {
    "Grameenphone": "GP",
    "Banglalink": "BL",
    "Robi": "ROBI",
    "Banjo": "BANJO"
}

# Function to extract client from Site Alias
def extract_clients(site_alias):
    if '(' in site_alias and ')' in site_alias:
        clients = site_alias.split('(')[1].strip(') ').split(', ')
        return [client for client in clients]
    return []

# Function to calculate duration in hours
def calculate_duration(start_time, end_time):
    duration = (end_time - start_time).total_seconds() / 3600
    return round(duration, 2)

# Load and process the Excel files
def load_data(outage_file, whole_month_file):
    outage_df = pd.read_excel(outage_file, sheet_name='RMS Alarm Elapsed Report', header=2)
    whole_month_df = pd.read_excel(whole_month_file, sheet_name='RMS Alarm Elapsed Report', header=2)
    return outage_df, whole_month_df

# Main function to run the Streamlit app
def main():
    st.title("Outage Data Processing")

    # File upload
    outage_file = st.file_uploader("Upload Outage Excel Data", type=['xlsx'])
    whole_month_file = st.file_uploader("Upload Whole Month Outage Excel Data", type=['xlsx'])
    dc_availability_file = st.file_uploader("Upload DC Availability Data", type=['xlsx'])

    if outage_file and whole_month_file:
        outage_df, whole_month_df = load_data(outage_file, whole_month_file)

        # Process outage data
        outage_df['Start Time'] = pd.to_datetime(outage_df['Start Time'])
        outage_df['End Time'] = pd.to_datetime(outage_df['End Time'])
        outage_df['Duration'] = outage_df.apply(lambda x: calculate_duration(x['Start Time'], x['End Time']), axis=1)

        # Initialize results storage
        results = {}

        # Group by Cluster and Zone
        for _, group in outage_df.groupby(['Cluster', 'Zone']):
            site_count = group['Site Alias'].nunique()
            event_count = group['Site Alias'].count()
            total_duration = group['Duration'].sum()
            
            if group['Cluster'].iloc[0] not in results:
                results[group['Cluster'].iloc[0]] = {}

            results[group['Cluster'].iloc[0]][group['Zone'].iloc[0]] = {
                'Site Count': site_count,
                'Duration': total_duration,
                'Event Count': event_count
            }

        # Create a table for display
        final_table = []

        for cluster, zones in results.items():
            for zone, metrics in zones.items():
                final_table.append({
                    'Region': cluster,
                    'Zone': zone,
                    'Site Count': metrics['Site Count'],
                    'Duration': f"{metrics['Duration']:.2f}",
                    'Event Count': metrics['Event Count']
                })

        final_df = pd.DataFrame(final_table)

        # Filter by client if needed
        clients = st.multiselect("Select Clients to Filter", options=list(tenant_mapping.keys()))
        
        if clients:
            final_df = final_df[final_df['Region'].isin(clients)]

        st.write(final_df)

        # Option to download the report
        if st.button("Download Report"):
            with pd.ExcelWriter('Outage_Report.xlsx') as writer:
                outage_df.to_excel(writer, sheet_name='Outage Data', index=False)
                final_df.to_excel(writer, sheet_name='Outage Report', index=False)

            st.success("Report has been saved as 'Outage_Report.xlsx'")

if __name__ == "__main__":
    main()
