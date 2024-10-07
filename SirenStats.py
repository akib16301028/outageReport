import streamlit as st
from playwright.sync_api import sync_playwright

# Streamlit app title
st.title("Automate Login to Banglalink UMS")

# User input fields for username and password (not visible to the user)
username = "r.parves@blmanagedservices.com"
password = "BLjessore@2024"

# Function to automate login
def automate_login(username, password):
    with sync_playwright() as p:
        # Launch the browser in headless mode
        browser = p.chromium.launch(headless=True)  # Set headless=True to run without opening a browser window
        page = browser.new_page()

        # Navigate to the login page
        page.goto("https://ums.banglalink.net/index.php/site/login")

        # Fill the login form
        page.fill('input[name="LoginForm[username]"]', username)
        page.fill('input[name="LoginForm[password]"]', password)

        # Click the login button
        page.click('button[type="submit"]')

        # Wait for the navigation after login (adjust the selector if necessary)
        page.wait_for_load_state('networkidle')

        # Optionally, you can navigate to the main page or take a screenshot for confirmation
        page.goto("https://ums.banglalink.net/index.php/site/dashboard")  # Example redirect URL after login

        # Screenshot of the logged-in page for confirmation (optional)
        page.screenshot(path="login_success.png")

        # Close the browser
        browser.close()

        return "Login attempt complete. You are now logged in."

# Automatically log in when the app runs
if st.button("Login"):
    result = automate_login(username, password)
    st.write(result)
    st.image("login_success.png")
