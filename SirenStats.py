import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os

# Function to set up the Chrome WebDriver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--headless")  # Run in headless mode for automation
    driver_service = Service('chromedriver')  # Ensure chromedriver is in your PATH
    driver = webdriver.Chrome(service=driver_service, options=chrome_options)
    return driver

# Function to download files
def download_files():
    driver = setup_driver()
    
    # First URL
    driver.get("https://ums.banglalink.net/index.php/site/login")
    time.sleep(2)
    
    # Log in to Banglalink
    driver.find_element(By.ID, "LoginForm_username").send_keys("r.parves@blmanagedservices.com")
    driver.find_element(By.ID, "LoginForm_password").send_keys("BLjessore@2024")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]").click()
    time.sleep(5)
    
    # Click the download button for alarms
    driver.get("https://ums.banglalink.net/index.php/alarms")
    time.sleep(2)
    driver.find_element(By.CLASS_NAME, "btn_csv_export").click()
    time.sleep(5)  # Wait for download to complete

    # Second URL
    driver.get("https://rms.eyeelectronics.net/login")
    time.sleep(2)
    
    # Log in to Eye Electronics
    driver.find_element(By.NAME, "userName").send_keys("noc@stl")
    driver.find_element(By.NAME, "password").send_keys("ScomNoC!2#")
    driver.find_element(By.XPATH, "//span[contains(text(), 'Login')]").click()
    time.sleep(5)
    
    # Navigate to RMS stations
    driver.find_element(By.XPATH, "//div[contains(text(), 'rms stations')]").click()
    time.sleep(2)
    
    # Select 'All' and export
    driver.find_element(By.XPATH, "//div[contains(@class, 'item-title')]/h4[contains(text(), 'All')]").click()
    time.sleep(2)
    driver.find_element(By.XPATH, "//span[contains(text(), 'Export')]").click()
    time.sleep(5)  # Wait for download to complete

    driver.quit()

# Streamlit app starts here
st.title("Alarm Data Processing App")

# Button to start downloading files
if st.button("Download Files"):
    download_files()
    st.success("Files downloaded successfully! Please upload them below.")

# File upload section
csv_file = st.file_uploader("Upload CSV file from Banglalink Alarms", type=["csv"])
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
