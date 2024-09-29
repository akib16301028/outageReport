# app.py

import streamlit as st
import pandas as pd
import sqlite3
import io

def main():
    st.title("SirenStats - Alarm Data Processing App")
    
    st.markdown("""
    **SirenStats** is a Streamlit application that processes alarm data from Banglalink and Eye Electronics. 
    Upload your CSV and XLSX files to generate a comprehensive report.
    """)
    
    st.header("Upload Your Files")
    
    # Upload CSV file from Banglalink Alarms
    csv_file = st.file_uploader("Upload CSV file from Banglalink Alarms", type=["csv"])
    
    # Upload XLSX file from Eye Electronics
    xlsx_file = st.file_uploader("Upload XLSX file from Eye Electronics", type=["xlsx"])
    
    if st.button("Process Data"):
        if csv_file and xlsx_file:
            try:
                # Read the CSV file
                csv_data = pd.read_csv(csv_file)
                st.success("CSV file uploaded and read successfully!")
    
                # Read the XLSX file
                xlsx_data = pd.read_excel(xlsx_file)
                st.success("XLSX file uploaded and read successfully!")
    
                # Validate required columns in CSV
                required_csv_columns = ["Alarm Raised Date", "Alarm Raised Time", "Active for", "Site", "Alarm Slogan"]
                if not all(col in csv_data.columns for col in required_csv_columns):
                    st.error(f"CSV file is missing one or more required columns: {required_csv_columns}")
                    st.stop()
    
                # Validate required columns in XLSX
                required_xlsx_columns = ["Site Alias", "Zone", "Cluster"]
                if not all(col in xlsx_data.columns for col in required_xlsx_columns):
                    st.error(f"XLSX file is missing one or more required columns: {required_xlsx_columns}")
                    st.stop()
    
                # Extract and clean relevant columns from CSV
                bl_df = csv_data[required_csv_columns].copy()
                bl_df['Site_Clean'] = bl_df['Site'].str.replace('_X', '', regex=False).str.split(' ').str[0].str.split('(').str[0].str.strip()
    
                # Extract and clean relevant columns from XLSX
                ee_df = xlsx_data[required_xlsx_columns].copy()
                ee_df['Site_Alias_Clean'] = ee_df['Site Alias'].str.split(' ').str[0].str.split('(').str[0].str.strip()
    
                # Merge dataframes on cleaned Site columns
                merged_df = pd.merge(bl_df, ee_df, left_on='Site_Clean', right_on='Site_Alias_Clean', how='left')
    
                # Check for unmatched sites
                unmatched = merged_df[merged_df['Zone'].isna()]
                if not unmatched.empty:
                    st.warning("Some sites did not match and have NaN for Zone and Cluster.")
                    st.write(unmatched[['Site', 'Site_Clean']])
    
                # Select and rename columns as needed
                final_df = merged_df[[
                    "Alarm Raised Date",
                    "Alarm Raised Time",
                    "Active for",
                    "Site",
                    "Alarm Slogan",
                    "Zone",
                    "Cluster"
                ]].copy()
    
                # Display the first few rows for verification
                st.header("Preview of Merged Data")
                st.dataframe(final_df.head())
    
                # Save to SQLite database (in-memory)
                conn = sqlite3.connect(":memory:")
                final_df.to_sql('alarms', conn, if_exists='replace', index=False)
                conn.close()
    
                # Provide download link for the final report
                st.header("Download Final Report")
                towrite = io.BytesIO()
                final_df.to_excel(towrite, index=False, engine='openpyxl')
                towrite.seek(0)
                st.download_button(
                    label="📥 Download Final Report as Excel",
                    data=towrite,
                    file_name="final_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
                st.success("Data processed and report generated successfully!")
    
            except Exception as e:
                st.error(f"An error occurred while processing the files: {e}")
        else:
            st.error("Please upload both CSV and XLSX files before processing.")

if __name__ == "__main__":
    main()
