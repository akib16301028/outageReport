import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Initialize Streamlit app
st.title("Banglalink Login Automation")
st.write("This app automates logging into the Banglalink portal and downloads a CSV file.")

# Set up Chrome options for headless execution
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Start a Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Go to the login page
login_url = "https://ums.banglalink.net/index.php/site/login"
driver.get(login_url)
st.write(f"Accessing {login_url}")

# Define user credentials (you mentioned these)
username = "r.parves@blmanagedservices.com"
password = "BLjessore@2024"

# Find the username and password fields and input the credentials
st.write("Filling in the username and password...")

try:
    driver.find_element(By.ID, "LoginForm_username").send_keys(username)
    driver.find_element(By.ID, "LoginForm_password").send_keys(password)

    # Click the login button
    login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"].btn-primary')
    login_button.click()

    st.write("Logging in...")

    # Wait for page to load
    time.sleep(5)

    # Check if login was successful
    if "dashboard" in driver.current_url:
        st.success("Logged in successfully!")

        # Now navigate to the page where the CSV button is located
        st.write("Navigating to the page with the CSV download button...")

        # Wait for the button to appear and then click it
        csv_button = driver.find_element(By.CSS_SELECTOR, 'button.btn_csv_export')
        csv_button.click()

        st.write("CSV download initiated!")

        # Wait for the download to complete
        time.sleep(5)

    else:
        st.error("Login failed. Please check your credentials.")
except Exception as e:
    st.error(f"An error occurred: {e}")

# Close the browser session
driver.quit()

st.write("Automation task completed.")
