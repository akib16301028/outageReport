import streamlit as st
from playwright.sync_api import sync_playwright
import pandas as pd
from io import BytesIO

# Function to perform login and download CSV from Banglalink
def login_and_download_csv_banglalink(login_url, username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=True for no GUI
        page = browser.new_page()
        
        # Step 1: Go to the login page
        page.goto(login_url)

        # Step 2: Fill the login form
        page.fill('input[name="LoginForm[username]"]', username)
        page.fill('input[name="LoginForm[password]"]', password)
        
        # Step 3: Submit the login form
        page.click('button[type="submit"]')

        # Wait for navigation after login
        page.wait_for_navigation()

        # Check if login was successful
        if 'Logout' not in page.content():
            st.error("Banglalink login failed. Please check your credentials.")
            return None
        
        st.success("Logged into Banglalink successfully!")

        # Step 4: Navigate to the page with the CSV download button
        csv_button_page_url = "https://ums.banglalink.net/index.php/alarms"  # Update this path if necessary
        page.goto(csv_button_page_url)

        # Step 5: Click the CSV download button
        page.click('button:has-text("CSV")')

        # Wait for the download to complete
        download = page.wait_for_event('download')

        # Step 6: Save the downloaded file
        path = download.path()
        with open(path, 'rb') as f:
            content = f.read()

        # Parse CSV content using pandas
        try:
            df = pd.read_csv(BytesIO(content))
            return df, content
        except Exception as e:
            st.error(f"Failed to parse Banglalink CSV: {e}")
            return None
        finally:
            browser.close()


# Function to perform login and download CSV from Eye Electronics
def login_and_download_csv_eye(login_url, username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=True for no GUI
        page = browser.new_page()
        
        # Step 1: Go to the login page
        page.goto(login_url)

        # Step 2: Fill the login form
        page.fill('input[name="userName"]', username)
        page.fill('input[name="password"]', password)
        
        # Step 3: Submit the login form
        page.click('button:has-text("Login")')

        # Wait for navigation after login
        page.wait_for_navigation()

        # Check if login was successful
        if 'Logout' not in page.content():
            st.error("Eye Electronics login failed. Please check your credentials.")
            return None
        
        st.success("Logged into Eye Electronics successfully!")

        # Step 4: Navigate to the page with the CSV download button
        csv_button_page_url = "https://rms.eyeelectronics.net/path/to/alarms"  # Update this path if necessary
        page.goto(csv_button_page_url)

        # Step 5: Click the CSV download button
        page.click('button.btn_csv_export')  # Adjust the selector if necessary

        # Wait for the download to complete
        download = page.wait_for_event('download')

        # Step 6: Save the downloaded file
        path = download.path()
        with open(path, 'rb') as f:
            content = f.read()

        # Parse CSV content using pandas
        try:
            df = pd.read_csv(BytesIO(content))
            return df, content
        except Exception as e:
            st.error(f"Failed to parse Eye Electronics CSV: {e}")
            return None
        finally:
            browser.close()

# Streamlit Interface
st.title("Portal Automation with Playwright")
st.write("This app logs into the Banglalink and Eye Electronics portals and downloads CSV files.")

# Accessing secrets from Streamlit's secrets management
try:
    username = st.secrets["credentials"]["username"]
    password = st.secrets["credentials"]["password"]
except KeyError:
    st.error("Credentials not found. Please ensure they are set in secrets.toml.")
    st.stop()

if st.button("Login and Download CSV from Banglalink"):
    login_url_banglalink = "https://ums.banglalink.net/index.php/site/login"
    
    result_banglalink = login_and_download_csv_banglalink(login_url_banglalink, username, password)
    
    if result_banglalink:
        df_banglalink, csv_content_banglalink = result_banglalink
        st.write("Banglalink CSV Data:")
        st.dataframe(df_banglalink)
        
        # Provide a download button
        st.download_button(
            label="Download Banglalink CSV",
            data=csv_content_banglalink,
            file_name="banglalink_data.csv",
            mime="text/csv",
        )

if st.button("Login and Download CSV from Eye Electronics"):
    login_url_eye = "https://rms.eyeelectronics.net/login"
    
    result_eye = login_and_download_csv_eye(login_url_eye, username, password)
    
    if result_eye:
        df_eye, csv_content_eye = result_eye
        st.write("Eye Electronics CSV Data:")
        st.dataframe(df_eye)
        
        # Provide a download button
        st.download_button(
            label="Download Eye Electronics CSV",
            data=csv_content_eye,
            file_name="eye_electronics_data.csv",
            mime="text/csv",
        )
