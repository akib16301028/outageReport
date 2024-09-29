# app.py

import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

# Ensure download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Function to set up the Chrome WebDriver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    # Uncomment the next line to run Chrome in headless mode
    # chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# Function to clear the download directory
def clear_download_directory():
    st.info("Clearing the download directory...")
    try:
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        st.success("Download directory cleared.")
    except Exception as e:
        st.error(f"Failed to clear download directory: {e}")

# Function to download Banglalink CSV
def download_banglalink_csv(driver):
    st.info("Navigating to Banglalink login page...")
    driver.get("https://ums.banglalink.net/index.php/site/login")
    time.sleep(2)

    # Log in to Banglalink
    st.info("Logging into Banglalink...")
    try:
        driver.find_element(By.ID, "LoginForm_username").send_keys("r.parves@blmanagedservices.com")
        driver.find_element(By.ID, "LoginForm_password").send_keys("BLjessore@2024")
        driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'btn-primary')]").click()
        time.sleep(5)
        st.success("Logged into Banglalink successfully.")
    except Exception as e:
        st.error(f"Error logging into Banglalink: {e}")
        return False

    # Navigate to Alarms page
    st.info("Navigating to Alarms page...")
    try:
        driver.get("https://ums.banglalink.net/index.php/alarms")
        time.sleep(3)
        st.success("Navigated to Alarms page.")
    except Exception as e:
        st.error(f"Error navigating to Alarms page: {e}")
        return False

    # Click CSV download button
    st.info("Initiating CSV download...")
    try:
        download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn_csv_export')]")
        download_button.click()
        st.success("CSV download initiated.")
    except Exception as e:
        st.error(f"Error initiating CSV download: {e}")
        return False

    # Wait for download to complete
    st.info("Waiting for CSV download to complete...")
    time.sleep(10)  # Adjust based on your internet speed

    # Rename the downloaded CSV file
    st.info("Renaming downloaded CSV file...")
    try:
        original_csv = os.path.join(DOWNLOAD_DIR, "alarms.csv")  # Adjust if the filename differs
        new_csv = os.path.join(DOWNLOAD_DIR, "alarms_report.csv")
        if os.path.exists(original_csv):
            os.rename(original_csv, new_csv)
            st.success(f"Renamed CSV to: alarms_report.csv")
        else:
            st.error("CSV file not found after download.")
            return False
    except Exception as e:
        st.error(f"Error renaming CSV file: {e}")
        return False

    return True

# Function to download Eye Electronics XLSX
def download_eyeelectronics_xlsx(driver):
    st.info("Navigating to Eye Electronics login page...")
    driver.get("https://rms.eyeelectronics.net/login")
    time.sleep(2)

    # Log in to Eye Electronics
    st.info("Logging into Eye Electronics...")
    try:
        driver.find_element(By.NAME, "userName").send_keys("noc@stl")
        driver.find_element(By.NAME, "password").send_keys("ScomNoC!2#")
        driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'p-button')]").click()
        time.sleep(5)
        st.success("Logged into Eye Electronics successfully.")
    except Exception as e:
        st.error(f"Error logging into Eye Electronics: {e}")
        return False

    # Navigate to RMS Stations
    st.info("Navigating to RMS Stations...")
    try:
        rms_stations = driver.find_element(By.XPATH, "//div[contains(@class, 'eye-menu-item') and contains(., 'rms stations')]")
        rms_stations.click()
        time.sleep(3)
        st.success("Navigated to RMS Stations.")
    except Exception as e:
        st.error(f"Error navigating to RMS Stations: {e}")
        return False

    # Click on "All" stations
    st.info("Selecting 'All' stations...")
    try:
        all_stations = driver.find_element(By.XPATH, "//div[@class='card-item']//h4[contains(text(), 'All')]")
        all_stations.click()
        time.sleep(3)
        st.success("Selected 'All' stations.")
    except Exception as e:
        st.error(f"Error selecting 'All' stations: {e}")
        return False

    # Click Export button
    st.info("Initiating XLSX export...")
    try:
        export_button = driver.find_element(By.XPATH, "//button[contains(@class, 'p-button') and contains(., 'Export')]")
        export_button.click()
        st.success("Export download initiated.")
    except Exception as e:
        st.error(f"Error initiating XLSX export: {e}")
        return False

    # Wait for download to complete
    st.info("Waiting for XLSX download to complete...")
    time.sleep(15)  # Adjust based on your internet speed

    # Rename the downloaded XLSX file
    st.info("Renaming downloaded XLSX file...")
    try:
        # Search for the latest XLSX file containing 'RMS Station Status Report'
        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".xlsx") and "RMS Station Status Report" in f]
        if files:
            latest_file = max([os.path.join(DOWNLOAD_DIR, f) for f in files], key=os.path.getmtime)
            new_xlsx = os.path.join(DOWNLOAD_DIR, "rms_station_report.xlsx")
            os.rename(latest_file, new_xlsx)
            st.success(f"Renamed XLSX to: rms_station_report.xlsx")
        else:
            st.error("XLSX file not found after download.")
            return False
    except Exception as e:
        st.error(f"Error renaming XLSX file: {e}")
        return False

    return True

# Function to automate downloads
def automate_downloads():
    clear_download_directory()
    driver = setup_driver()
    try:
        success_banglalink = download_banglalink_csv(driver)
        if not success_banglalink:
            st.error("Failed to download Banglalink CSV.")
            return False

        success_eyeelectronics = download_eyeelectronics_xlsx(driver)
        if not success_eyeelectronics:
            st.error("Failed to download Eye Electronics XLSX.")
            return False

        st.success("All files downloaded and renamed successfully.")
        return True

    finally:
        driver.quit()
        st.info("Browser closed.")

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
        required_csv_columns = ["Alarm Raised Date", "Alarm Raised Time", "Active for", "Site", "Alarm Slogan"]
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
            "Active for",
            "Site",
            "Alarm Slogan",
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
    
    st.markdown("""
    **SirenStats** is a Streamlit application that automates the download of alarm data from Banglalink and Eye Electronics,
    allows you to manually upload the downloaded files, processes the data by merging relevant information, 
    and generates a comprehensive report.
    """)
    
    st.header("Automate Downloading Files")
    st.markdown("""
    Click the button below to automatically download the required CSV and XLSX files from Banglalink and Eye Electronics.
    Ensure that Chrome is installed on your machine and that no other Chrome instances are running.
    """)
    
    if st.button("Download Files"):
        automate_success = automate_downloads()
        if automate_success:
            st.success("Files downloaded and renamed successfully!")
        else:
            st.error("Failed to download one or more files.")

    st.header("Upload and Process Files")
    st.markdown("""
    After downloading, you can manually upload the CSV and XLSX files to process and generate the final report.
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
