# download.py

import os
import time
import pandas as pd
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

def setup_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    # Uncomment the next line to run Chrome in headless mode
    # chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def download_banglalink_csv(driver):
    print("Navigating to Banglalink login page...")
    driver.get("https://ums.banglalink.net/index.php/site/login")
    time.sleep(2)

    # Log in
    print("Logging into Banglalink...")
    driver.find_element(By.ID, "LoginForm_username").send_keys("r.parves@blmanagedservices.com")
    driver.find_element(By.ID, "LoginForm_password").send_keys("BLjessore@2024")
    driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'btn-primary')]").click()
    time.sleep(5)

    # Navigate to Alarms page
    print("Navigating to Alarms page...")
    driver.get("https://ums.banglalink.net/index.php/alarms")
    time.sleep(3)

    # Click CSV download button
    print("Clicking CSV download button...")
    try:
        download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn_csv_export')]")
        download_button.click()
        print("CSV download initiated.")
    except Exception as e:
        print(f"Error finding or clicking CSV download button: {e}")
        return

    # Wait for download to complete
    time.sleep(10)  # Adjust based on file size and internet speed

    # Rename the downloaded CSV file
    original_csv = os.path.join(DOWNLOAD_DIR, "alarms.csv")  # Adjust if the filename differs
    new_csv = os.path.join(DOWNLOAD_DIR, "alarms_report.csv")
    if os.path.exists(original_csv):
        os.rename(original_csv, new_csv)
        print(f"Renamed CSV to: {new_csv}")
    else:
        print("CSV file not found after download.")

def download_eyeelectronics_xlsx(driver):
    print("Navigating to Eye Electronics login page...")
    driver.get("https://rms.eyeelectronics.net/login")
    time.sleep(2)

    # Log in
    print("Logging into Eye Electronics...")
    driver.find_element(By.NAME, "userName").send_keys("noc@stl")
    driver.find_element(By.NAME, "password").send_keys("ScomNoC!2#")
    driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'p-button')]").click()
    time.sleep(5)

    # Navigate to RMS Stations
    print("Navigating to RMS Stations...")
    try:
        rms_stations = driver.find_element(By.XPATH, "//div[contains(@class, 'eye-menu-item') and contains(., 'rms stations')]")
        rms_stations.click()
        print("Clicked RMS Stations.")
    except Exception as e:
        print(f"Error navigating to RMS Stations: {e}")
        return

    time.sleep(5)

    # Click on "All" stations
    print("Selecting 'All' stations...")
    try:
        all_stations = driver.find_element(By.XPATH, "//div[@class='card-item']//h4[contains(text(), 'All')]")
        all_stations.click()
        print("Clicked 'All' stations.")
    except Exception as e:
        print(f"Error selecting 'All' stations: {e}")
        return

    time.sleep(5)

    # Click Export button
    print("Clicking Export button...")
    try:
        export_button = driver.find_element(By.XPATH, "//button[contains(@class, 'p-button') and contains(., 'Export')]")
        export_button.click()
        print("Export download initiated.")
    except Exception as e:
        print(f"Error finding or clicking Export button: {e}")
        return

    # Wait for download to complete
    time.sleep(15)  # Adjust based on file size and internet speed

    # Rename the downloaded XLSX file
    # The filename format: RMS Station Status Report(September 30th 2024, 1_33_01 am).xlsx
    # We'll search for the latest XLSX file containing 'RMS Station Status Report'
    files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".xlsx") and "RMS Station Status Report" in f]
    if files:
        latest_file = max([os.path.join(DOWNLOAD_DIR, f) for f in files], key=os.path.getmtime)
        new_xlsx = os.path.join(DOWNLOAD_DIR, "rms_station_report.xlsx")
        os.rename(latest_file, new_xlsx)
        print(f"Renamed XLSX to: {new_xlsx}")
    else:
        print("XLSX file not found after download.")

def main():
    driver = setup_driver()
    try:
        download_banglalink_csv(driver)
        download_eyeelectronics_xlsx(driver)
    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()
