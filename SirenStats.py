import streamlit as st
import pandas as pd
import os

# Set the title of the Streamlit app
st.title("Alarm Data Processing App")

# Upload CSV file
csv_file = st.file_uploader("Upload CSV file from Banglalink Alarms", type=["csv"])
# Upload XLSX file
xlsx_file = st.file_uploader("Upload XLSX file from Eye Electronics", type=["xlsx"])

if csv_file and xlsx_file:
    # Read the CSV file
    csv_data = pd.read_csv(csv_file)
    
    # Read the XLSX file
    xlsx_data = pd.read_excel(xlsx_file)
    
    # Prepare to merge data
    merged_data = []

    for _, row in csv_data.iterrows():
        site_name = row['Site']
        # Process site name to match with Site Alias in the XLSX file
        processed_site_name = site_name.replace("_X", "").split(" (")[0]
        
        # Find the matching zone and cluster
        matching_row = xlsx_data[xlsx_data['Site Alias'].str.contains(processed_site_name, na=False, regex=False)]
        
        if not matching_row.empty:
            zone = matching_row['Zone'].values[0]
            cluster = matching_row['Cluster'].values[0]
            merged_data.append({
                "Alarm Raised Date": row["Alarm Raised Date"],
                "Alarm Raised Time": row["Alarm Raised Time"],
                "Active for": row["Active for"],
                "Site": site_name,
                "Alarm Slogan": row["Alarm Slogan"],
                "Zone": zone,
                "Cluster": cluster
            })

    # Create a DataFrame from merged data
    final_df = pd.DataFrame(merged_data)

    # Save the final DataFrame to a new Excel file
    final_output_filename = "final_report.xlsx"
    final_df.to_excel(final_output_filename, index=False)

    # Provide download link for the final report
    st.success("Data processed successfully!")
    st.write("Download the final report:")
    st.download_button(
        label="Download Final Report",
        data=final_df.to_excel(index=False, engine='openpyxl'),
        file_name=final_output_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("Please upload both CSV and XLSX files to process the data.")
