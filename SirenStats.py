from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os

# Set up Chrome options (this will enable file downloads)
chrome_options = Options()

# Optional: run in headless mode if needed
# chrome_options.add_argument("--headless")  

# Set preferences for the default download directory (use the same for both URLs)
download_dir = "/path/to/your/download/directory"  # Update this to your preferred download folder
prefs = {"download.default_directory": download_dir}
chrome_options.add_experimental_option("prefs", prefs)

# Set up WebDriver Manager for Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

####### PHASE 1 ########
# Step 1: Open the first login page (Banglalink)
driver.get("https://ums.banglalink.net/index.php/site/login")

# Give the page some time to load
time.sleep(2)

# Step 2: Locate the username and password fields and input credentials
username_field = driver.find_element(By.ID, "LoginForm_username")
password_field = driver.find_element(By.ID, "LoginForm_password")

# Input your credentials
username_field.send_keys("r.parves@blmanagedservices.com")
password_field.send_keys("BLjessore@2024")

# Step 3: Locate and click the login button
login_button = driver.find_element(By.XPATH, '//button[@type="submit" and contains(@class, "btn-primary")]')
login_button.click()

# Wait for the next page to load
time.sleep(5)

# Step 4: Locate the CSV download button and click it
csv_download_button = driver.find_element(By.XPATH, '//button[contains(@class, "btn_csv_export")]')
csv_download_button.click()

# Wait for the download to complete (adjust the time as needed)
time.sleep(10)  # Increase if the download takes longer

# Optionally, check if the file is downloaded in the specified directory
if os.path.exists(download_dir):
    print("First CSV file downloaded successfully!")

# Give some delay before moving to the next phase
time.sleep(2)

####### PHASE 2 ########
# Step 5: Open the second login page (Eye Electronics)
driver.get("https://rms.eyeelectronics.net/login")

# Give the page some time to load
time.sleep(2)

# Step 6: Locate the username and password fields and input credentials
username_field = driver.find_element(By.NAME, "userName")
password_field = driver.find_element(By.NAME, "password")

# Input your credentials
username_field.send_keys("noc@stl")
password_field.send_keys("ScomNoC!2#")

# Step 7: Locate and click the login button
login_button = driver.find_element(By.XPATH, '//button[@type="submit" and @label="Login"]')
login_button.click()

# Wait for the next page to load
time.sleep(5)

# Step 8: Click on "RMS Stations"
rms_stations_button = driver.find_element(By.XPATH, '//div[contains(@class, "eye-menu-item") and contains(., "rms stations")]')
rms_stations_button.click()

# Wait for the page to load
time.sleep(5)

# Step 9: Click on "All" stations (focus on the label 'All')
all_stations_button = driver.find_element(By.XPATH, '//div[@class="card-item"]//h4[contains(text(), "All")]')
all_stations_button.click()

# Wait for the page to load
time.sleep(5)

# Step 10: Click on the Export button
export_button = driver.find_element(By.XPATH, '//button[contains(@class, "p-button") and contains(., "Export")]')
export_button.click()

# Wait for the download to complete (adjust the time as needed)
time.sleep(10)  # Increase if the download takes longer

# Optionally, check if the file is downloaded in the specified directory
if os.path.exists(download_dir):
    print("Second CSV file downloaded successfully!")

# Close the browser after completing both phases
driver.quit()
