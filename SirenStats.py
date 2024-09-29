import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import tempfile

def download_csv():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Use a temporary directory for downloads
    download_dir = tempfile.gettempdir()
    prefs = {"download.default_directory": download_dir}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # PHASE 1: Banglalink login and download
    driver.get("https://ums.banglalink.net/index.php/site/login")
    time.sleep(2)

    username_field = driver.find_element(By.ID, "LoginForm_username")
    password_field = driver.find_element(By.ID, "LoginForm_password")
    username_field.send_keys(st.secrets["banglalink_username"])  # Use secrets for sensitive data
    password_field.send_keys(st.secrets["banglalink_password"])

    login_button = driver.find_element(By.XPATH, '//button[@type="submit" and contains(@class, "btn-primary")]')
    login_button.click()

    time.sleep(5)
    csv_download_button = driver.find_element(By.XPATH, '//button[contains(@class, "btn_csv_export")]')
    csv_download_button.click()

    time.sleep(10)

    # PHASE 2: Eye Electronics login and download
    driver.get("https://rms.eyeelectronics.net/login")
    time.sleep(2)

    username_field = driver.find_element(By.NAME, "userName")
    password_field = driver.find_element(By.NAME, "password")
    username_field.send_keys(st.secrets["eye_username"])  # Use secrets for sensitive data
    password_field.send_keys(st.secrets["eye_password"])

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

    time.sleep(10)
    driver.quit()

    return "CSV files downloaded successfully!"

# Streamlit UI
st.title("CSV Downloader App")
if st.button("Download CSVs"):
    with st.spinner("Downloading..."):
        result = download_csv()
        st.success(result)
