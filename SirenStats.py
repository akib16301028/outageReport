import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from io import BytesIO
import time  # Import time module for sleep

# Function to perform login and download CSV from Banglalink
def login_and_download_csv_banglalink(login_url, username, password):
    with requests.Session() as session:
        # Step 1: Get the login page to retrieve any hidden form data (e.g., CSRF tokens)
        login_page = session.get(login_url)
        if login_page.status_code != 200:
            st.error(f"Failed to access Banglalink login page. Status code: {login_page.status_code}")
            return None
        
        # Parse the login page
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Find the login form
        login_form = soup.find('form')
        if not login_form:
            st.error("Banglalink login form not found.")
            return None
        
        # Extract form action (URL to submit the form)
        form_action = login_form.get('action')
        post_url = urljoin(login_url, form_action)
        
        # Prepare payload with credentials
        payload = {}
        for input_tag in login_form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name == 'LoginForm[username]':
                payload[name] = username
            elif name == 'LoginForm[password]':
                payload[name] = password
            else:
                payload[name] = value  # Include other hidden fields like CSRF tokens
        
        # Submit the login form
        response = session.post(post_url, data=payload)
        if response.status_code != 200:
            st.error(f"Banglalink login failed. Status code: {response.status_code}")
            return None
        
        # Check if login was successful by checking the presence of a logout link
        if 'Logout' not in response.text:
            st.error("Banglalink login failed. Please check your credentials.")
            return None
        
        st.success("Logged into Banglalink successfully!")
        
        # Step 2: Wait for 2 seconds to allow the page to load completely
        time.sleep(2)
        
        # Navigate to the page with the CSV download button
        csv_button_page_url = "https://ums.banglalink.net/index.php/alarms"  # Update this path if necessary
        page = session.get(csv_button_page_url)
        if page.status_code != 200:
            st.error(f"Failed to access the page with CSV button. Status code: {page.status_code}")
            return None
        
        page_soup = BeautifulSoup(page.text, 'html.parser')
        
        # Find the CSV download button using the <span> containing "CSV"
        csv_button = page_soup.find('span', string='CSV')
        if not csv_button:
            st.error("Banglalink CSV download button not found.")
            return None
        
        # Extract the parent button that contains the download functionality
        csv_button_parent = csv_button.find_parent('button')
        if csv_button_parent and 'data-url' in csv_button_parent.attrs:
            csv_download_url = csv_button_parent['data-url']
        else:
            st.error("Banglalink CSV download URL not found.")
            return None
        
        # Construct full CSV download URL
        csv_download_url = urljoin(csv_button_page_url, csv_download_url)
        
        # Download the CSV file
        csv_response = session.get(csv_download_url)
        if csv_response.status_code != 200:
            st.error(f"Failed to download Banglalink CSV. Status code: {csv_response.status_code}")
            return None
        
        # Parse CSV content using pandas
        try:
            df = pd.read_csv(BytesIO(csv_response.content))
            return df, csv_response.content
        except Exception as e:
            st.error(f"Failed to parse Banglalink CSV: {e}")
            return None


# Function to perform login and download CSV from Eye Electronics
def login_and_download_csv_eye(login_url, username, password):
    with requests.Session() as session:
        # Step 1: Get the login page to retrieve any hidden form data
        login_page = session.get(login_url)
        if login_page.status_code != 200:
            st.error(f"Failed to access Eye Electronics login page. Status code: {login_page.status_code}")
            return None
        
        # Parse the login page
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Find the login form
        login_form = soup.find('form')
        if not login_form:
            st.error("Eye Electronics login form not found.")
            return None
        
        # Extract form action
        form_action = login_form.get('action')
        post_url = urljoin(login_url, form_action)
        
        # Prepare payload with credentials
        payload = {
            'userName': username,
            'password': password
        }
        
        # Submit the login form
        response = session.post(post_url, data=payload)
        if response.status_code != 200:
            st.error(f"Eye Electronics login failed. Status code: {response.status_code}")
            return None
        
        # Check if login was successful
        if 'Logout' not in response.text:
            st.error("Eye Electronics login failed. Please check your credentials.")
            return None
        
        st.success("Logged into Eye Electronics successfully!")
        
        # Step 2: Wait for 2 seconds to allow the page to load completely
        time.sleep(2)
        
        # Navigate to the page with the CSV download button
        csv_button_page_url = "https://rms.eyeelectronics.net/path/to/alarms"  # Update this path if necessary
        csv_button_page = session.get(csv_button_page_url)
        if csv_button_page.status_code != 200:
            st.error(f"Failed to access the page with the CSV button. Status code: {csv_button_page.status_code}")
            return None
        
        page_soup = BeautifulSoup(csv_button_page.text, 'html.parser')
        
        # Find the CSV download button
        csv_button = page_soup.find('button', class_='btn_csv_export')  # Adjust the class if necessary
        if not csv_button:
            st.error("Eye Electronics CSV download button not found.")
            return None
        
        # Get the CSV download URL from the button
        csv_download_url = csv_button.get('data-url')  # Adjust based on the actual data attribute
        
        # Download the CSV file
        csv_response = session.get(csv_download_url)
        if csv_response.status_code != 200:
            st.error(f"Failed to download Eye Electronics CSV. Status code: {csv_response.status_code}")
            return None
        
        # Parse CSV content using pandas
        try:
            df = pd.read_csv(BytesIO(csv_response.content))
            return df, csv_response.content
        except Exception as e:
            st.error(f"Failed to parse Eye Electronics CSV: {e}")
            return None

# Streamlit Interface
st.title("Portal Automation")
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
