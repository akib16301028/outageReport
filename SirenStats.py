import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os
import glob

# Function to set up Selenium WebDriver
def setup_driver(download_dir):
    chrome_options = Options()
    # Run in headless mode for server environments
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver
    except Exception as e:
        st.error(f"Error initializing WebDriver: {e}")
        st.stop()

# Function to download CSV from Banglalink
def download_banglalink_csv(driver, download_dir, username, password):
    try:
        driver.get("https://ums.banglalink.net/index.php/site/login")
        time.sleep(2)
        
        username_field = driver.find_element(By.ID, "LoginForm_username")
        password_field = driver.find_element(By.ID, "LoginForm_password")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.XPATH, '//button[@type="submit" and contains(@class, "btn-primary")]')
        login_button.click()
        
        time.sleep(5)
        
        csv_download_button = driver.find_element(By.XPATH, '//button[contains(@class, "btn_csv_export")]')
        csv_download_button.click()
        
        time.sleep(10)  # Adjust as needed
    except Exception as e:
        st.error(f"Error during Banglalink CSV download: {e}")
        driver.quit()
        st.stop()

# Function to download CSV from Eye Electronics
def download_eyeelectronics_csv(driver, download_dir, username, password):
    try:
        driver.get("https://rms.eyeelectronics.net/login")
        time.sleep(2)
        
        username_field = driver.find_element(By.NAME, "userName")
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.XPATH, '//button[@type="submit" and @label="Login"]')
        login_button.click()
        
        time.sleep(5)
        
        rms_stations_button = driver.find_element(By.XPATH, '//div[contains(@class, "eye-menu-item") and contains(., "rms stations")]')
        rms_stations_button.click()
        
        time.sleep(5)
        
        all_stations_button = driver.find_element(By.XPATH, '//div[@class="card-item"]//h4[contains(text(), "All")]')
        all_stations_button.click()
        
        time.sleep(5)
        
        export_button = driver.find_element(By.XPATH, '//button[contains(@class, "p-button") and contains(., "Export")]')
        export_button.click()
        
        time.sleep(10)  # Adjust as needed
    except Exception as e:
        st.error(f"Error during Eye Electronics CSV download: {e}")
        driver.quit()
        st.stop()

# Function to get the latest downloaded file
def get_latest_file(download_dir, extension="csv"):
    list_of_files = glob.glob(os.path.join(download_dir, f"*.{extension}"))
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def main():
    st.title("Automated CSV Downloader")

    st.markdown("""
    This application automates the downloading of CSV files from Banglalink and Eye Electronics platforms.
    """)

    # Define download directory
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)

    # Initialize session state to store file paths
    if 'banglalink_file' not in st.session_state:
        st.session_state.banglalink_file = None
    if 'eyeelectronics_file' not in st.session_state:
        st.session_state.eyeelectronics_file = None

    # Button to download Banglalink CSV
    if st.button("Download Banglalink CSV"):
        with st.spinner("Downloading Banglalink CSV..."):
            driver = setup_driver(download_dir)
            download_banglalink_csv(
                driver,
                download_dir,
                st.secrets["banglalink"]["username"],
                st.secrets["banglalink"]["password"]
            )
            driver.quit()
            latest_file = get_latest_file(download_dir)
            if latest_file:
                st.session_state.banglalink_file = latest_file
                st.success("Banglalink CSV downloaded successfully!")
            else:
                st.error("Failed to download Banglalink CSV.")

    # Button to download Eye Electronics CSV
    if st.button("Download Eye Electronics CSV"):
        with st.spinner("Downloading Eye Electronics CSV..."):
            driver = setup_driver(download_dir)
            download_eyeelectronics_csv(
                driver,
                download_dir,
                st.secrets["eyeelectronics"]["username"],
                st.secrets["eyeelectronics"]["password"]
            )
            driver.quit()
            latest_file = get_latest_file(download_dir)
            if latest_file:
                st.session_state.eyeelectronics_file = latest_file
                st.success("Eye Electronics CSV downloaded successfully!")
            else:
                st.error("Failed to download Eye Electronics CSV.")

    # Display download links
    st.header("Downloaded Files")

    if st.session_state.banglalink_file:
        try:
            with open(st.session_state.banglalink_file, "rb") as file:
                st.download_button(
                    label="Download Banglalink CSV",
                    data=file,
                    file_name=os.path.basename(st.session_state.banglalink_file),
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error reading Banglalink CSV file: {e}")

    if st.session_state.eyeelectronics_file:
        try:
            with open(st.session_state.eyeelectronics_file, "rb") as file:
                st.download_button(
                    label="Download Eye Electronics CSV",
                    data=file,
                    file_name=os.path.basename(st.session_state.eyeelectronics_file),
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error reading Eye Electronics CSV file: {e}")

if __name__ == "__main__":
    main()
