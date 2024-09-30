# app.py

import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import shutil
import requests
from bs4 import BeautifulSoup

# Function to download Banglalink CSV
def download_banglalink_csv(session, login_url, alarms_url, username, password):
    """
    Logs into Banglalink and downloads the alarms CSV file.
    """
    # Fetch the login page to get any hidden form inputs (e.g., CSRF tokens)
    response = session.get(login_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract hidden form inputs if any
    hidden_inputs = soup.find_all("input", type="hidden")
    form_data = {inp.get('name'): inp.get('value') for inp in hidden_inputs}

    # Add username and password to form data
    form_data['LoginForm[username]'] = username
    form_data['LoginForm[password]'] = password

    # Submit the login form
    login_response = session.post(login_url, data=form_data)
    
    # Check if login was successful
    if login_response.url != alarms_url:
        st.error("Failed to log into Banglalink.")
        return None

    # Navigate to alarms page
    alarms_response = session.get(alarms_url)
    alarms_soup = BeautifulSoup(alarms_response.text, 'html.parser')

    # Find the CSV download button/link
    download_button = alarms_soup.find("button", class_="btn_csv_export")
    if not download_button:
        st.error("CSV download button not found on Banglalink alarms page.")
        return None

    # Assuming the button triggers a direct file download via a link or an API endpoint
    # Here, we'll simulate clicking the button by finding the download URL

    # Example: If the button has a data-href attribute
    download_url = download_button.get('data-href')
    if not download_url:
        # Alternative approach: Check if the button triggers a direct download via JavaScript
        # This might not work as expected without executing JavaScript
        st.error("Download URL not found for Banglalink CSV.")
        return None

    # Complete the download URL if it's relative
    download_url = requests.compat.urljoin(alarms_url, download_url)

    # Download the CSV file
    csv_response = session.get(download_url)
    if csv_response.status_code != 200:
        st.error("Failed to download Banglalink CSV file.")
        return None

    return csv_response.content

# Function to download Eye Electronics XLSX
def download_eyeelectronics_xlsx(session, login_url, export_url, username, password):
    """
    Logs into Eye Electronics and downloads the RMS Stations XLSX file.
    """
    # Fetch the login page to get any hidden form inputs (e.g., CSRF tokens)
    response = session.get(login_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract hidden form inputs if any
    hidden_inputs = soup.find_all("input", type="hidden")
    form_data = {inp.get('name'): inp.get('value') for inp in hidden_inputs}

    # Add username and password to form data
    form_data['userName'] = username
    form_data['password'] = password

    # Submit the login form
    login_response = session.post(login_url, data=form_data)
    
    # Check if login was successful by verifying the redirected URL or presence of specific elements
    if login_response.url == login_url:
        st.error("Failed to log into Eye Electronics.")
        return None

    # Navigate to RMS Stations page
    rms_response = session.get(export_url)
    rms_soup = BeautifulSoup(rms_response.text, 'html.parser')

    # Find the 'Export' button/link
    export_button = rms_soup.find("button", text=lambda x: x and "Export" in x)
    if not export_button:
        st.error("Export button not found on Eye Electronics RMS Stations page.")
        return None

    # Assuming the button triggers a direct file download via a link or an API endpoint
    # Extract the download URL
    download_url = export_button.get('data-href')
    if not download_url:
        # Alternative approach: Check if the button triggers a direct download via JavaScript
        st.error("Download URL not found for Eye Electronics XLSX.")
        return None

    # Complete the download URL if it's relative
    download_url = requests.compat.urljoin(export_url, download_url)

    # Download the XLSX file
    xlsx_response = session.get(download_url)
    if xlsx_response.status_code != 200:
        st.error("Failed to download Eye Electronics XLSX file.")
        return None

    return xlsx_response.content

# Function to process uploaded files
def process_files(csv_content, xlsx_content):
    try:
        # Read the CSV file
        csv_data = pd.read_csv(io.StringIO(csv_content.decode('utf-8')))
        st.success("CSV file uploaded and read successfully!")

        # Read the XLSX file with header in row 3 (zero-based index 2)
        xlsx_data = pd.read_excel(io.BytesIO(xlsx_content), header=2)
        st.success("XLSX file uploaded and read successfully!")

        # Display columns for debugging
        st.subheader("CSV File Columns")
        st.write(csv_data.columns.tolist())

        st.subheader("XLSX File Columns")
        st.write(xlsx_data.columns.tolist())

        # Validate required columns in CSV
        required_csv_columns = ["Alarm Raised Date", "Alarm Raised Time", "Site", "Alarm Slogan", "Service Type", "Mini-Hub", "Power Status"]
        missing_csv_columns = [col for col in required_csv_columns if col not in csv_data.columns]
        if missing_csv_columns:
            st.error(f"CSV file is missing one or more required columns: {missing_csv_columns}")
            st.stop()

        # Validate required columns in XLSX
        required_xlsx_columns = ["Site Alias", "Zone", "Cluster"]
        missing_xlsx_columns = [col for col in required_xlsx_columns if col not in xlsx_data.columns]
        if missing_xlsx_columns:
            st.error(f"XLSX file is missing one or more required columns: {missing_xlsx_columns}")
            st.stop()

        # Extract and clean relevant columns from CSV
        bl_df = csv_data[required_csv_columns].copy()
        bl_df['Site_Clean'] = (
            bl_df['Site']
            .str.replace('_X', '', regex=False)  # Remove '_X'
            .str.split(' ').str[0]               # Remove anything after space
            .str.split('(').str[0]               # Remove anything after '('
            .str.strip()                          # Trim whitespace
        )

        # Extract and clean relevant columns from XLSX
        ee_df = xlsx_data[required_xlsx_columns].copy()
        ee_df['Site_Alias_Clean'] = (
            ee_df['Site Alias']
            .str.replace(r'\s*\(.*\)', '', regex=True)  # Remove anything after space and '('
            .str.strip()
        )

        # Display cleaned columns for debugging
        st.subheader("Cleaned CSV 'Site' Column")
        st.write(bl_df['Site_Clean'].head())

        st.subheader("Cleaned XLSX 'Site Alias' Column")
        st.write(ee_df['Site_Alias_Clean'].head())

        # Merge dataframes on cleaned Site columns
        merged_df = pd.merge(
            bl_df, 
            ee_df[['Site_Alias_Clean', 'Site Alias', 'Zone', 'Cluster']], 
            left_on='Site_Clean', 
            right_on='Site_Alias_Clean', 
            how='left'
        )

        # Check for unmatched sites
        unmatched = merged_df[merged_df['Zone'].isna()]
        if not unmatched.empty:
            st.warning("Some sites did not match and have NaN for Zone and Cluster.")
            st.write(unmatched[['Site', 'Site_Clean']])

        # Select and rename columns as needed
        final_df = merged_df[[
            "Alarm Raised Date",
            "Alarm Raised Time",
            "Site",
            "Alarm Slogan",
            "Service Type",
            "Mini-Hub",
            "Power Status",
            "Site Alias",  # Include 'Site Alias' from XLSX
            "Zone",
            "Cluster"
        ]].copy()

        # Display the first few rows for verification
        st.header("Preview of Merged Data")
        st.dataframe(final_df.head())

        # Optionally, save to SQLite database (in-memory)
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

    # Function to automate downloads
    def automate_downloads():
        st.header("Automate Downloading Files")

        # User credentials (consider securing these in a more secure way)
        st.subheader("Banglalink Credentials")
        bl_username = st.text_input("Banglalink Username", type="email")
        bl_password = st.text_input("Banglalink Password", type="password")

        st.subheader("Eye Electronics Credentials")
        ee_username = st.text_input("Eye Electronics Username", type="text")
        ee_password = st.text_input("Eye Electronics Password", type="password")

        if st.button("Download Files Automatically"):
            if not all([bl_username, bl_password, ee_username, ee_password]):
                st.error("Please provide all credentials to proceed.")
                return

            with st.spinner("Downloading files..."):
                session = requests.Session()

                # URLs (Adjust these based on actual website structure)
                bl_login_url = "https://ums.banglalink.net/index.php/site/login"
                bl_alarms_url = "https://ums.banglalink.net/index.php/alarms"

                ee_login_url = "https://rms.eyeelectronics.net/login"
                ee_export_url = "https://rms.eyeelectronics.net/export"

                # Download Banglalink CSV
                bl_csv_content = download_banglalink_csv(
                    session, 
                    bl_login_url, 
                    bl_alarms_url, 
                    bl_username, 
                    bl_password
                )

                if bl_csv_content:
                    # Provide download button for CSV
                    st.subheader("Banglalink CSV Download")
                    st.download_button(
                        label="📥 Download Banglalink CSV",
                        data=bl_csv_content,
                        file_name="alarms_report.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Failed to download Banglalink CSV.")

                # Download Eye Electronics XLSX
                ee_xlsx_content = download_eyeelectronics_xlsx(
                    session, 
                    ee_login_url, 
                    ee_export_url, 
                    ee_username, 
                    ee_password
                )

                if ee_xlsx_content:
                    # Provide download button for XLSX
                    st.subheader("Eye Electronics XLSX Download")
                    st.download_button(
                        label="📥 Download Eye Electronics XLSX",
                        data=ee_xlsx_content,
                        file_name="rms_station_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("Failed to download Eye Electronics XLSX.")

    # Streamlit app starts here
    def main():
        st.title("SirenStats - Alarm Data Processing App")
        
        st.markdown("""
        **SirenStats** is a Streamlit application that automates the downloading of alarm data from Banglalink and Eye Electronics,
        allows manual uploading of these files, processes the data by merging relevant information, and generates a comprehensive report.
        """)
        
        # Sidebar for navigation
        st.sidebar.title("Navigation")
        app_mode = st.sidebar.selectbox("Choose the app mode",
                                        ["Automate Download and Upload", "Only Upload and Process"])
        
        if app_mode == "Automate Download and Upload":
            # Automate Download Section
            automate_downloads()
            
            st.markdown("---")
            
            # File upload and processing section
            st.header("Upload and Process Files")
            st.markdown("""
            After downloading the files, you can upload them here to process and generate the final report.
            """)
            
            # File upload section
            csv_file = st.file_uploader("Upload CSV file from Banglalink Alarms", type=["csv"])
            xlsx_file = st.file_uploader("Upload XLSX file from Eye Electronics", type=["xlsx"])
    
            if st.button("Process Uploaded Files"):
                if csv_file and xlsx_file:
                    process_files(csv_file.getvalue(), xlsx_file.getvalue())
                else:
                    st.error("Please upload both CSV and XLSX files before processing.")
        
        elif app_mode == "Only Upload and Process":
            # Only Upload and Process Section
            st.header("Upload and Process Files")
            st.markdown("""
            Manually upload the CSV and XLSX files to process and generate the final report.
            """)
    
            # File upload section
            csv_file = st.file_uploader("Upload CSV file from Banglalink Alarms", type=["csv"])
            xlsx_file = st.file_uploader("Upload XLSX file from Eye Electronics", type=["xlsx"])
    
            if st.button("Process Uploaded Files"):
                if csv_file and xlsx_file:
                    process_files(csv_file.getvalue(), xlsx_file.getvalue())
                else:
                    st.error("Please upload both CSV and XLSX files before processing.")
    
    if __name__ == "__main__":
        main()
