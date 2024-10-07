import streamlit as st
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os

def install_playwright_browsers():
    """
    Install Playwright browsers if not already installed.
    This function runs only once to install the necessary browser binaries.
    """
    if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
        st.info("Installing Playwright browsers. This may take a few minutes...")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.install()
        st.success("Playwright browsers installed successfully.")

def perform_login(username: str, password: str):
    """
    Uses Playwright to automate logging into the specified website.
    
    Args:
        username (str): The username/email for login.
        password (str): The corresponding password.
        
    Returns:
        bool: True if login is successful, False otherwise.
        str: Additional message or error details.
    """
    try:
        with sync_playwright() as p:
            # Launch the browser in headless mode
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to the login page
            page.goto("https://ums.banglalink.net/index.php/site/login", timeout=60000)
            
            # Wait for the username field to be visible
            page.wait_for_selector("#LoginForm_username", timeout=10000)
            
            # Fill in the username and password
            page.fill("#LoginForm_username", username)
            page.fill("#LoginForm_password", password)
            
            # Click the login button
            page.click("button.btn.btn-primary.block.full-width.m-b")
            
            # Wait for navigation or a specific element that signifies successful login
            try:
                # Replace the selector below with an actual selector that appears after successful login
                page.wait_for_selector("selector_for_dashboard_or_unique_element", timeout=15000)
                login_successful = True
                message = "Login successful!"
            except PlaywrightTimeoutError:
                # If the specific element isn't found, assume login failed
                login_successful = False
                message = "Login failed. Please check your credentials or the website status."
            
            # Close the browser
            browser.close()
            
            return login_successful, message

    except Exception as e:
        return False, f"An error occurred during the login process: {str(e)}"

def main():
    st.title("Automated Website Login using Playwright")
    st.write("This app automates logging into [Banglalink UM](https://ums.banglalink.net/index.php/site/login) using Playwright.")
    
    st.header("Login Credentials")
    
    # Retrieve credentials from Streamlit Secrets or allow user input
    # It's highly recommended to use Streamlit's Secrets Management for sensitive data
    # For demonstration, default values are provided
    username = st.text_input("Username", value=st.secrets["credentials"]["username"] if "credentials" in st.secrets else "")
    password = st.text_input("Password", type="password", value=st.secrets["credentials"]["password"] if "credentials" in st.secrets else "")
    
    if st.button("Login"):
        if not username or not password:
            st.error("Please provide both username and password.")
            return
        
        # Install Playwright browsers if not already installed
        install_playwright_browsers()
        
        with st.spinner("Attempting to log in..."):
            success, msg = perform_login(username, password)
        
        if success:
            st.success(msg)
        else:
            st.error(msg)

if __name__ == "__main__":
    main()
