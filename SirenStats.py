import streamlit as st
from playwright.sync_api import sync_playwright

def login_and_download_csv_eye(login_url, username, password):
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)  # Use headless mode
            page = browser.new_page()
            page.goto(login_url)

            # Fill in the login form
            page.fill('input[name="userName"]', username)
            page.fill('input[name="password"]', password)
            page.click('button:has-text("Login")')

            # Wait for navigation
            page.wait_for_navigation()

            # Navigate to the CSV download page
            # Make sure to update the URL accordingly
            csv_page_url = "https://rms.eyeelectronics.net/path/to/csv_page"
            page.goto(csv_page_url)

            # Click the CSV download button
            page.click('button:has-text("CSV")')

            # Wait for the download to complete (You might need to adjust this based on the actual behavior)
            page.wait_for_timeout(2000)

            # Get the downloaded CSV content (Adjust this part based on how the CSV is served)
            csv_content = page.content()  # This is just an example; you might need to download it differently

            browser.close()
            return csv_content
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None
