# app.py

import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import shutil
import time

from playwright.sync_api import sync_playwright

# Function to set up the download directory
def setup_download_directory():
    download_dir = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    return download_dir

# Function to automate downloading using Playwright
def automate_download(download_dir):
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            downloads_path=download_dir
        )
        page = context.new_page()

        # ---------------------------
        # Download Banglalink Alarms CSV
        # ---------------------------
        st.info("Downloading Banglalink Alarms CSV...")

        try:
            # Navigate to Banglalink login page
            page.goto("https://ums.banglalink.net/index.php/site/login")
            time.sleep(2)  # Wait for page to load

            # Fill in login form
            page.fill("input#LoginForm_username", "r.parves@blmanagedservices.com")
            page.fill("input#LoginForm_password", "BLjessore@2024")

            # Click the login button
            page.click("button.btn-primary")

            # Wait for navigation after login
            page.wait_for_url("https://ums.banglalink.net/index.php/dashboard", timeout=10000)

            st.success("Logged into Banglalink successfully.")

            # Navigate to Alarms page
            page.goto("https://ums.banglalink.net/index.php/alarms")
            time.sleep(2)  # Wait for page to load

            # Click the CSV download button and wait for download
            with page.expect_download() as download_info:
                page.click("button.btn_csv_export")
            download = download_info.value
            download.save_as(os.path.join(download_dir, "alarms_report.csv"))

            st.success("Banglalink Alarms CSV downloaded successfully.")

        except Exception as e:
            st.error(f"Failed to download Banglalink Alarms CSV: {e}")

        # ---------------------------
        # Download Eye Electronics XLSX
        # ---------------------------
        st.info("Downloading Eye Electronics XLSX...")

        try:
            # Navigate to Eye Electronics login page
            page.goto("https://rms.eyeelectronics.net/login")
            time.sleep(2)  # Wait for page to load

            # Fill in login form
            page.fill("input[name='userName']", "noc@stl")
            page.fill("input[name='password']", "ScomNoC!2#")

            # Click the login button
            page.click("button[type='submit']")

            # Wait for navigation after login
            page.wait_for_url("https://rms.eyeelectronics.net/dashboard", timeout=10000)

            st.success("Logged into Eye Electronics successfully.")

            # Navigate to RMS Stations page
            page.goto("https://rms.eyeelectronics.net/rms-stations")
            time.sleep(2)  # Wait for page to load

            # Click on "All" stations
            page.click("h4:has-text('All')")

            # Click the Export button and wait for download
            with page.expect_download() as download_info:
                page.click("button:has-text('Export')")
            download = download_info.value
            download.save_as(os.path.join(download_dir, "rms_station_report.xlsx"))

            st.success("Eye Electronics XLSX downloaded successfully.")

        except Exception as e:
            st.error(f"Failed to download Eye Electronics XLSX: {e}")

        # Close browser
        browser.close()
        st.info("Automated downloads completed and browser closed.")

# Function to process uploaded files
def process_files(csv_file, xlsx_file):
    try:
        # Read the CSV file
        csv_data = pd.read_csv(csv_file)
        st.success("CSV file uploaded and read successfully!")

        # Read the XLSX file with header in row 3 (zero-based index 2)
        xlsx_data = pd.read_excel(xlsx_file, header=2)
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

    except Exception as e:
        st.error(f"An error occurred while processing the files: {e}")

# Streamlit app starts here
def main():
    st.title("SirenStats - Alarm Data Processing App")

    st.markdown("""\
    **SirenStats** is a Streamlit application that automates the downloading of alarm data from Banglalink and Eye Electronics,
    processes the data by merging relevant information, and generates a comprehensive report.
    """)

    st.header("Automate File Downloads")
    st.markdown("""
    Click the button below to automatically download the required CSV and XLSX files from Banglalink and Eye Electronics.
    """)

    if st.button("Download Files Automatically"):
        download_dir = setup_download_directory()
        automate_download(download_dir)
        st.success(f"Files downloaded and saved in the `downloads` directory.")

    st.header("Upload and Process Files")
    st.markdown("""
    If you prefer to download the files manually or after the automated download completes, you can upload them here to process and generate the final report.
    """)

    # File upload section
    csv_file = st.file_uploader("Upload CSV file from Banglalink Alarms", type=["csv"])
    xlsx_file = st.file_uploader("Upload XLSX file from Eye Electronics", type=["xlsx"])

    if st.button("Process Uploaded Files"):
        if csv_file and xlsx_file:
            process_files(csv_file, xlsx_file)
        else:
            st.error("Please upload both CSV and XLSX files before processing.")

if __name__ == "__main__":
    main()
