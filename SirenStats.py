import streamlit as st
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import pandas as pd
from io import BytesIO

# Function to perform login and download CSV using Playwright
def login_and_download_csv_playwright(username, password):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Go to the login page
            login_url = "https://ums.banglalink.net/index.php/site/login"
            page.goto(login_url)
            st.write(f"Accessing {login_url}")

            # Fill in the username and password
            st.write("Filling in the username and password...")
            page.fill('input#LoginForm_username', username)
            page.fill('input#LoginForm_password', password)

            # Click the login button
            st.write("Clicking the login button...")
            page.click('button[type="submit"].btn-primary')

            # Wait for navigation after login
            st.write("Waiting for login to complete...")
            try:
                # Wait for a specific element that appears after login
                page.wait_for_selector('.some-dashboard-class', timeout=20000)  # Adjust selector as needed
                st.success("Logged in successfully!")
            except PlaywrightTimeoutError:
                st.warning("Login may have failed or dashboard element not found. Proceeding to locate CSV button.")

            # Additional sleep to ensure the page is fully loaded
            page.wait_for_timeout(5000)  # 5 seconds

            # Locate and click the CSV download button
            st.write("Locating the CSV download button...")
            try:
                # Wait until the CSV button is visible and clickable
                page.wait_for_selector('button.dt-button.btn.btn-default.btn-sm.btn_csv_export', timeout=10000)
                page.click('button.dt-button.btn.btn-default.btn-sm.btn_csv_export')
                st.success("CSV download initiated!")
            except PlaywrightTimeoutError:
                st.error("CSV download button not found or not clickable.")
                browser.close()
                return None

            # Wait for the download to complete
            st.write("Waiting for the CSV file to download...")
            try:
                with page.expect_download() as download_info:
                    page.click('button.dt-button.btn.btn-default.btn-sm.btn_csv_export')
                download = download_info.value
                csv_path = download.path()
                csv_content = download.body()
                st.success("CSV file downloaded successfully!")
            except PlaywrightTimeoutError:
                st.error("CSV download timed out.")
                browser.close()
                return None

            # Close the browser
            browser.close()

            return csv_content

    except Exception as e:
        st.error(f"An error occurred during automation: {e}")
        return None

# Streamlit Interface
st.title("Banglalink Portal Automation with Playwright")
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
        csv_data = login_and_download_csv_playwright(username, password)
        if csv_data:
            # Create a DataFrame from CSV content
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
