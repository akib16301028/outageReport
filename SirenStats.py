import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Streamlit layout for user interaction
st.title('Automated Website Login using Selenium')
st.write("This app demonstrates how to log in to a website using Selenium with Streamlit.")

# User inputs for login credentials
username = st.text_input("Username", value="r.parves@blmanagedservices.com")
password = st.text_input("Password", type="password", value="BLjessore@2024")

if st.button('Login'):
    # Initialize the WebDriver (assuming Chrome)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # Navigate to the login page
    driver.get('https://ums.banglalink.net/index.php/site/login')

    # Allow page to load
    time.sleep(3)

    # Find the username and password fields, and input the credentials
    driver.find_element(By.ID, "LoginForm_username").send_keys(username)
    driver.find_element(By.ID, "LoginForm_password").send_keys(password)

    # Click the login button
    driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.block.full-width.m-b").click()

    # Allow time for the next page to load
    time.sleep(5)

    # Capture the title or some other element to confirm login success
    if "dashboard" in driver.title.lower():
        st.success("Login successful!")
    else:
        st.error("Login failed. Please check your credentials or the website status.")

    # Close the browser
    driver.quit()
