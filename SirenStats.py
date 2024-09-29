# app.py
import streamlit as st
from playwright.sync_api import sync_playwright
import os
import glob
import time
import shutil

# Hard-coded credentials (Not recommended for production)
BANGALINK_USERNAME = "r.parves@blmanagedservices.com"
BANGALINK_PASSWORD = "BLjessore@2024"

EYEELECTRONICS_USERNAME = "noc@stl"
EYEELECTRONICS_PASSWORD = "ScomNoC!2#"

# Function to ensure Playwright browsers are installed
def install_playwright_browsers():
    with sync_playwright() as p:
        p.install()

# Call the installation function
# Note: This may not work on Streamlit Cloud due to permission restrictions
try:
    install_playwright_browsers()
except Exception as e:
    st.warning("Playwright browsers installation skipped. They might already be installed.")

# Function to download CSV from Banglalink
def download_banglalink_csv(download_dir, username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        page.goto("https://ums.banglalink.net/index.php/site/login")
        
        # Input credentials
        page.fill("#LoginForm_username", username)
        page.fill("#LoginForm_password", password)
        
        # Click login
        page.click('button[type="submit"].btn-primary')
        
        # Wait for navigation to complete
        page.wait_for_load_state("networkidle")
        
        # Click CSV download button
        with page.expect_download() as download_info:
            page.click('button.btn_csv_export')
        download = download_info.value
        download_path = os.path.join(download_dir, download.suggested_filename)
        download.save_as(download_path)
        
        browser.close()

# Function to download CSV from Eye Electronics
def download_eyeelectronics_csv(download_dir, username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        page.goto("https://rms.eyeelectronics.net/login")
        
        # Input credentials
        page.fill('input[name="userName"]', username)
        page.fill('input[name="password"]', password)
        
        # Click login
        page.click('button[type="submit"][label="Login"]')
        
        # Wait for navigation to complete
        page.wait_for_load_state("networkidle")
        
        # Click on "RMS Stations"
        page.click('div.eye-menu-item:has-text("rms stations")')
        page.wait_for_load_state("networkidle")
        
        # Click on "All" stations
        page.click('div.card-item >> text=All')
        page.wait_for_load_state("networkidle")
        
        # Click on Export button
        with page.expect_download() as download_info:
            page.click('button.p-button:has-text("Export")')
        download = download_info.value
        download_path = os.path.join(download_dir, download.suggested_filename)
        download.save_as(download_path)
        
        browser.close()

# Function to get the latest downloaded file
def get_latest_file(download_dir, extension="csv"):
    list_of_files = glob.glob(os.path.join(download_dir, f"*.{extension}"))
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def main():
    st.title("Automated CSV Downloader")
    
    st.markdown("""
    This application automates the downloading of CSV files from Banglalink and Eye Electronics platforms.
    """)
    
    # Define download directory
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    # Initialize session state to store file paths
    if 'banglalink_file' not in st.session_state:
        st.session_state.banglalink_file = None
    if 'eyeelectronics_file' not in st.session_state:
        st.session_state.eyeelectronics_file = None
    
    # Button to download Banglalink CSV
    if st.button("Download Banglalink CSV"):
        with st.spinner("Downloading Banglalink CSV..."):
            try:
                download_banglalink_csv(
                    download_dir,
                    BANGALINK_USERNAME,
                    BANGALINK_PASSWORD
                )
                latest_file = get_latest_file(download_dir)
                if latest_file:
                    st.session_state.banglalink_file = latest_file
                    st.success("Banglalink CSV downloaded successfully!")
                else:
                    st.error("Failed to download Banglalink CSV.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    
    # Button to download Eye Electronics CSV
    if st.button("Download Eye Electronics CSV"):
        with st.spinner("Downloading Eye Electronics CSV..."):
            try:
                download_eyeelectronics_csv(
                    download_dir,
                    EYEELECTRONICS_USERNAME,
                    EYEELECTRONICS_PASSWORD
                )
                latest_file = get_latest_file(download_dir)
                if latest_file:
                    st.session_state.eyeelectronics_file = latest_file
                    st.success("Eye Electronics CSV downloaded successfully!")
                else:
                    st.error("Failed to download Eye Electronics CSV.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    
    # Display download links
    st.header("Downloaded Files")
    
    if st.session_state.banglalink_file:
        try:
            with open(st.session_state.banglalink_file, "rb") as file:
                st.download_button(
                    label="Download Banglalink CSV",
                    data=file,
                    file_name=os.path.basename(st.session_state.banglalink_file),
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error reading Banglalink CSV file: {e}")
    
    if st.session_state.eyeelectronics_file:
        try:
            with open(st.session_state.eyeelectronics_file, "rb") as file:
                st.download_button(
                    label="Download Eye Electronics CSV",
                    data=file,
                    file_name=os.path.basename(st.session_state.eyeelectronics_file),
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error reading Eye Electronics CSV file: {e}")

if __name__ == "__main__":
    main()
