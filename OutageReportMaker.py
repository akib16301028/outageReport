import streamlit as st
from playwright.sync_api import sync_playwright
import os

# Streamlit app title
st.title("Automate Login to Banglalink UMS")

# Hardcoded credentials (for demonstration only, use environment variables in production)
username = "r.parves@blmanagedservices.com"
password = "BLjessore@2024"

# Function to automate login
def automate_login(username, password):
    try:
        with sync_playwright() as p:
            # Launch the browser in headless mode (set headless=False for debugging)
            browser = p.chromium.launch(headless=True)  # Change to False to see the browser
            page = browser.new_page()

            # Navigate to the login page
            page.goto("https://ums.banglalink.net/index.php/site/login")

            # Fill the login form
            page.fill('input[name="LoginForm[username]"]', username)
            page.fill('input[name="LoginForm[password]"]', password)

            # Click the login button
            page.click('button[type="submit"]')

            # Wait for the navigation after login
            page.wait_for_load_state('networkidle')

            # Navigate to the main page after login
            page.goto("https://ums.banglalink.net/index.php/site/dashboard")  # Adjust to the correct URL

            # Screenshot of the logged-in page for confirmation
            page.screenshot(path="login_success.png")

            # Close the browser
            browser.close()

            return "Login attempt complete. You are now logged in."

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Automatically log in when the app runs
if st.button("Login"):
    result = automate_login(username, password)
    st.write(result)

    # Check if the image exists before displaying
    if os.path.exists("login_success.png"):
        st.image("login_success.png")
    else:
        st.warning("No screenshot available.")
