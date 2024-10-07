import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    st.title('Automated Website Login using Selenium')
    st.write("This app demonstrates how to log in to a website using Selenium with Streamlit.")

    # Securely retrieve credentials (recommended)
    # It's better to use Streamlit's secrets management instead of hardcoding
    # For demonstration, we'll use hardcoded values as per your original request
    username = st.text_input("Username", value="r.parves@blmanagedservices.com")
    password = st.text_input("Password", type="password", value="BLjessore@2024")

    if st.button('Login'):
        try:
            st.info("Initializing browser...")

            # Set up headless Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Initialize WebDriver with webdriver-manager to handle driver installation
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            st.success("Browser initialized successfully.")

            # Navigate to the login page
            st.info("Navigating to the login page...")
            driver.get('https://ums.banglalink.net/index.php/site/login')

            # Wait for the username field to be present
            wait = WebDriverWait(driver, 10)
            username_field = wait.until(EC.presence_of_element_located((By.ID, "LoginForm_username")))
            password_field = wait.until(EC.presence_of_element_located((By.ID, "LoginForm_password")))

            # Input credentials
            st.info("Entering credentials...")
            username_field.send_keys(username)
            password_field.send_keys(password)

            # Click the login button
            st.info("Attempting to log in...")
            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.block.full-width.m-b")))
            login_button.click()

            # Allow time for login to process
            time.sleep(5)

            # Verify login by checking the page title or a specific element
            if "dashboard" in driver.title.lower():
                st.success("Login successful!")
            else:
                st.error("Login failed. Please check your credentials or the website status.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

        finally:
            # Ensure the browser is closed regardless of success or failure
            driver.quit()
            st.info("Browser closed.")

if __name__ == "__main__":
    main()
