import streamlit as st
from playwright.sync_api import sync_playwright
import tempfile

def download_csv():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # PHASE 1: Banglalink login and download
            page.goto("https://ums.banglalink.net/index.php/site/login")
            page.fill("#LoginForm_username", st.secrets["banglalink"]["username"])
            page.fill("#LoginForm_password", st.secrets["banglalink"]["password"])
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000)

            # Click on the CSV download button
            page.click('button.btn_csv_export')
            page.wait_for_timeout(10000)  # Wait for the download to complete

            # PHASE 2: Eye Electronics login and download
            page.goto("https://rms.eyeelectronics.net/login")
            page.fill('[name="userName"]', st.secrets["eye"]["username"])
            page.fill('[name="password"]', st.secrets["eye"]["password"])
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000)

            # Navigate and download
            page.click('//div[contains(@class, "eye-menu-item") and contains(., "rms stations")]')
            page.wait_for_timeout(5000)
            page.click('//div[@class="card-item"]//h4[contains(text(), "All")]')
            page.wait_for_timeout(5000)
            page.click('//button[contains(@class, "p-button") and contains(., "Export")]')
            page.wait_for_timeout(10000)  # Wait for the download to complete

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            browser.close()

    return "CSV files downloaded successfully!"

# Streamlit UI
st.title("CSV Downloader App")
if st.button("Download CSVs"):
    with st.spinner("Downloading..."):
        result = download_csv()
        st.success(result)
