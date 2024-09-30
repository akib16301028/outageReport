import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from io import BytesIO

# Function to perform login and download CSV
def login_and_download_csv(login_url, csv_button_url, username, password):
    with requests.Session() as session:
        # Step 1: Get the login page to retrieve any hidden form data (e.g., CSRF tokens)
        login_page = session.get(login_url)
        if login_page.status_code != 200:
            st.error(f"Failed to access login page. Status code: {login_page.status_code}")
            return None
        
        # Parse the login page
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Find the login form
        login_form = soup.find('form')
        if not login_form:
            st.error("Login form not found on the login page.")
            return None
        
        # Extract form action (URL to submit the form)
        form_action = login_form.get('action')
        if not form_action:
            st.error("Login form action not found.")
            return None
        
        # Construct the full login URL
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
            st.error(f"Login failed. Status code: {response.status_code}")
            return None
        
        # Check if login was successful by checking the presence of a logout link or dashboard element
        dashboard_soup = BeautifulSoup(response.text, 'html.parser')
        if dashboard_soup.find('a', text='Logout') is None:
            st.error("Login failed. Please check your credentials.")
            return None
        
        st.success("Logged in successfully!")
        
        # Step 2: Navigate to the page with the CSV download button
        csv_button_page_url = response.url  # Change if needed
        page = session.get(csv_button_page_url)
        if page.status_code != 200:
            st.error(f"Failed to access the page with CSV button. Status code: {page.status_code}")
            return None
        
        page_soup = BeautifulSoup(page.text, 'html.parser')
        
        # Find the CSV download button
        csv_button = page_soup.find('button', {'class': 'dt-button btn btn-default btn-sm btn_csv_export'})
        if not csv_button:
            st.error("CSV download button not found.")
            return None
        
        # Extract the CSV download URL
        csv_download_url = csv_button.get('data-url')
        if not csv_download_url:
            st.error("CSV download URL not found in the button attributes.")
            return None
        
        # Construct full CSV download URL
        csv_download_url = urljoin(csv_button_page_url, csv_download_url)
        
        # Download the CSV file
        csv_response = session.get(csv_download_url)
        if csv_response.status_code != 200:
            st.error(f"Failed to download CSV. Status code: {csv_response.status_code}")
            return None
        
        # Parse CSV content using pandas
        try:
            df = pd.read_csv(BytesIO(csv_response.content))
            return df, csv_response.content
        except Exception as e:
            st.error(f"Failed to parse CSV: {e}")
            return None

# Streamlit Interface
st.title("Banglalink Portal Automation")
st.write("This app logs into the Banglalink portal and downloads a CSV file.")

# Accessing secrets from Streamlit's secrets management
try:
    username = st.secrets["credentials"]["username"]
    password = st.secrets["credentials"]["password"]
except KeyError:
    st.error("Credentials not found. Please ensure they are set in secrets.toml.")
    st.stop()

if st.button("Login and Download CSV"):
    login_url = "https://ums.banglalink.net/index.php/site/login"
    
    result = login_and_download_csv(login_url, login_url, username, password)
    
    if result:
        df, csv_content = result
        st.write("CSV Data:")
        st.dataframe(df)
        
        # Provide a download button
        st.download_button(
            label="Download CSV",
            data=csv_content,
            file_name="downloaded_data.csv",
            mime="text/csv",
        )
