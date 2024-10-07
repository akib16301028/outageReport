import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Streamlit layout
st.title('Automated Website Login using Selenium')
st.write("This app demonstrates how to log in to a website using Selenium with Streamlit.")

# Securely retrieve credentials (recommended)
# It's better to use Streamlit's secrets management instead of hardcoding
# For demonstration, we'll use hardcoded values as per your original request
username = st.text_input("Username", value="r.parves@blmanagedservices.com")
password = st.text_input("Password", type="password", value="BLjessore@2024")

if st.button('Login'):
    try:
        # Initialize WebDriver with webdriver-manager to handle driver installation
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        
        # Navigate to the login page
        driver.get('https://ums.banglalink.net/index.php/site/login')
        
        # Allow the page to load
        time.sleep(3)
        
        # Find username and password fields and input credentials
        driver.find_element(By.ID, "LoginForm_username").send_keys(username)
        driver.find_element(By.ID, "LoginForm_password").send_keys(password)
        
        # Click the login button
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.block.full-width.m-b").click()
        
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
