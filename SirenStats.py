import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from io import BytesIO

# Function to perform login and download CSV
def login_and_download_csv(username, password):
    try:
        # Set up Chrome options for headless execution
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress logs

        # Initialize WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Define wait
        wait = WebDriverWait(driver, 20)  # 20 seconds timeout

        # Go to the login page
        login_url = "https://ums.banglalink.net/index.php/site/login"
        driver.get(login_url)
        st.write(f"Accessing {login_url}")

        # Wait for the username field to be present
        wait.until(EC.presence_of_element_located((By.ID, "LoginForm_username")))

        # Input username and password
        st.write("Filling in the username and password...")
        driver.find_element(By.ID, "LoginForm_username").send_keys(username)
        driver.find_element(By.ID, "LoginForm_password").send_keys(password)

        # Click the login button
        st.write("Clicking the login button...")
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"].btn-primary')
        login_button.click()

        # Wait for the dashboard or a specific element that signifies a successful login
        st.write("Waiting for login to complete...")
        try:
            # Adjust the expected condition based on the post-login page
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "some-dashboard-class")))
            st.success("Logged in successfully!")
        except TimeoutException:
            # If specific element not found, proceed to try locating the CSV button
            st.warning("Login may have failed or dashboard element not found. Proceeding to locate CSV button.")

        # Alternatively, wait for the URL to change or another condition
        time.sleep(5)  # Additional sleep to ensure the page is fully loaded

        # Attempt to find the CSV download button
        st.write("Locating the CSV download button...")
        try:
            # Wait until the CSV button is clickable
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.dt-button.btn.btn-default.btn-sm.btn_csv_export')))
            csv_button = driver.find_element(By.CSS_SELECTOR, 'button.dt-button.btn.btn-default.btn-sm.btn_csv_export')
            csv_button.click()
            st.success("CSV download initiated!")
        except TimeoutException:
            st.error("CSV download button not found or not clickable.")
            driver.quit()
            return None

        # Wait for the download to complete
        st.write("Waiting for the CSV file to download...")
        time.sleep(5)  # Adjust based on download time

        # Assuming the CSV is downloaded to a specific directory, fetch it
        # Since Selenium cannot directly fetch the downloaded file in headless mode,
        # you might need to set the download directory and read the file.
        # Alternatively, if the download triggers a direct response, capture it.

        # For demonstration, let's assume the CSV is returned as a response or accessible via a link.
        # Implementing this requires more details about the download mechanism.

        # Placeholder for CSV content
        csv_content = b""  # Replace with actual content if accessible

        # Close the browser
        driver.quit()

        # Return CSV content
        return csv_content

    except Exception as e:
        st.error(f"An error occurred during automation: {e}")
        return None

# Streamlit Interface
st.title("Banglalink Portal Automation")
st.write("This app logs into the Banglalink portal and attempts to download a CSV file.")

# **Security Best Practice:** Use Streamlit's secrets management for credentials
try:
    username = st.secrets["credentials"]["username"]
    password = st.secrets["credentials"]["password"]
except KeyError:
    st.error("Credentials not found. Please ensure they are set in `secrets.toml`.")
    st.stop()

if st.button("Login and Download CSV"):
    with st.spinner("Automating login and CSV download..."):
        csv_data = login_and_download_csv(username, password)
        if csv_data:
            # Assuming you have the CSV content, you can create a DataFrame
            try:
                df = pd.read_csv(BytesIO(csv_data))
                st.write("CSV Data:")
                st.dataframe(df)

                # Provide a download button
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="downloaded_data.csv",
                    mime="text/csv",
                )
            except Exception as e:
                st.error(f"Failed to process CSV data: {e}")
        else:
            st.error("Failed to download CSV.")

st.write("Automation task completed.")
