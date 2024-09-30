# app.py

import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import shutil
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Function to set up the Chrome WebDriver
def setup_driver(download_dir):
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# Function to download Banglalink CSV
def download_banglalink_csv(driver, download_dir):
    st.info("Downloading Banglalink Alarms CSV...")
    driver.get("https://ums.banglalink.net/index.php/site/login")
    time.sleep(2)

    # Log in to Banglalink
    driver.find_element(By.ID, "LoginForm_username").send_keys("r.parves@blmanagedservices.com")
    driver.find_element(By.ID, "LoginForm_password").send_keys("BLjessore@2024")
    driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary')]").click()
    time.sleep(5)

    # Navigate to Alarms page
    driver.get("https://ums.banglalink.net/index.php/alarms")
    time.sleep(2)

    # Click CSV download button
    try:
        download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn_csv_export')]")
        download_button.click()
        st.success("Banglalink Alarms CSV download initiated.")
    except Exception as e:
        st.error(f"Failed to initiate Banglalink CSV download: {e}")
        return

    # Wait for download to complete
    time.sleep(10)  # Adjust based on file size and internet speed

    # Rename the downloaded CSV file
    original_csv = os.path.join(download_dir, "alarms.csv")  # Adjust if filename differs
    new_csv = os.path.join(download_dir, "alarms_report.csv")
    if os.path.exists(original_csv):
        os.rename(original_csv, new_csv)
        st.success(f"Renamed CSV to: {new_csv}")
    else:
        st.error("CSV file not found after download.")

# Function to download Eye Electronics XLSX
def download_eye_electronics_xlsx(driver, download_dir):
    st.info("Downloading Eye Electronics XLSX...")
    driver.get("https://rms.eyeelectronics.net/login")
    time.sleep(2)

    # Log in to Eye Electronics
    driver.find_element(By.NAME, "userName").send_keys("noc@stl")
    driver.find_element(By.NAME, "password").send_keys("ScomNoC!2#")
    driver.find_element(By.XPATH, "//button[contains(@class, 'p-button-label') and span[text()='Login']]").click()
    time.sleep(5)

    # Navigate to RMS Stations
    try:
        driver.find_element(By.XPATH, "//span[text()='rms stations']").click()
        st.success("Navigated to RMS Stations.")
    except Exception as e:
        st.error(f"Failed to navigate to RMS Stations: {e}")
        return

    time.sleep(2)

    # Click on "All" stations
    try:
        driver.find_element(By.XPATH, "//h4[text()='All']").click()
        st.success("Clicked on 'All' stations.")
    except Exception as e:
        st.error(f"Failed to click on 'All' stations: {e}")
        return

    time.sleep(2)

    # Click Export button
    try:
        driver.find_element(By.XPATH, "//span[text()='Export']").click()
        st.success("Export download initiated.")
    except Exception as e:
        st.error(f"Failed to initiate Export download: {e}")
        return

    # Wait for download to complete
    time.sleep(15)  # Adjust based on file size and internet speed

    # Rename the downloaded XLSX file
    # Assuming filename pattern: RMS Station Status Report(September 30th 2024, 1_33_01 am).xlsx
    files = [f for f in os.listdir(download_dir) if f.endswith(".xlsx") and "RMS Station Status Report" in f]
    if files:
        latest_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getmtime)
        new_xlsx = os.path.join(download_dir, "rms_station_report.xlsx")
        os.rename(latest_file, new_xlsx)
        st.success(f"Renamed XLSX to: {new_xlsx}")
    else:
        st.error("XLSX file not found after download.")

# Function to download files automatically
def automate_download():
    download_dir = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    driver = setup_driver(download_dir)
    
    try:
        download_banglalink_csv(driver, download_dir)
        download_eye_electronics_xlsx(driver, download_dir)
    finally:
        driver.quit()
        st.info("Browser closed after downloading.")

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
    **SirenStats** is a Streamlit application that processes alarm data by merging relevant information
    from Banglalink and Eye Electronics and generates a comprehensive report.
    """)

    st.header("Automate File Downloads")
    st.markdown("""
    Click the button below to automatically download the required CSV and XLSX files from Banglalink and Eye Electronics.
    """)

    if st.button("Download Files Automatically"):
        automate_download()

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
