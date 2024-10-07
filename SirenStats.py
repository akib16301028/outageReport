import streamlit as st
from playwright.sync_api import sync_playwright

# Streamlit app title
st.title("Automate Login to Banglalink UMS")

# User input fields for username and password
username = st.text_input("Enter Username", "r.parves@blmanagedservices.com")
password = st.text_input("Enter Password", type="password", value="BLjessore@2024")

# Function to automate login
def automate_login(username, password):
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=False)  # Set headless=True to run without opening a browser window
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

        # Screenshot for confirmation
        page.screenshot(path="login_success.png")

        # Close the browser
        browser.close()

        return "Login attempt complete. Check the browser for the result."

# Streamlit button to trigger the login function
if st.button("Login"):
    result = automate_login(username, password)
    st.write(result)
    st.image("login_success.png")
