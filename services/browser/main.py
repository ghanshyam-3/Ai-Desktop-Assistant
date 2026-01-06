from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import uvicorn
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = FastAPI(title="Browser Control Service")

driver = None

def get_driver():
    global driver
    if driver is None:
        options = webdriver.ChromeOptions()
    if driver is None:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless") 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("user-data-dir=./chrome_profile") # Disabled to prevent crash
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

@app.get("/")
def home():
    return {"status": "Browser Service Running", "port": 8002}

import os

# CONFIGURATION
# Set your desired profile directory name here. 
# Common values: "Default", "Profile 1", "Profile 2".
# Check chrome://version in your browser to see the "Profile Path" last folder name.
CHROME_PROFILE = "Default"

@app.post("/open-url")
def open_url(url: str):
    """Opens a URL in a SPECIFIC Chrome profile."""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        
        print(f"Opening URL in Chrome Profile '{CHROME_PROFILE}': {url}")
        
        # Command to open specific profile. 
        # "start chrome" usually works if Chrome is in PATH.
        # We append --profile-directory to proper argument chain.
        os.system(f'start chrome "{url}" --profile-directory="{CHROME_PROFILE}"')
        
    except Exception as e:
        print(f"Browser Error: {e}")
        return {"status": "error", "message": str(e)}
        
    return {"status": "success", "message": f"Opened {url}"}

@app.post("/search")
def search_google(query: str):
    """Searches Google in specific Chrome profile."""
    try:
        url = f"https://www.google.com/search?q={query}"
        print(f"Searching in Chrome Profile '{CHROME_PROFILE}': {url}")
        os.system(f'start chrome "{url}" --profile-directory="{CHROME_PROFILE}"')
        
    except Exception as e:
        print(f"Browser Error: {e}")
        return {"status": "error", "message": str(e)}
        
    return {"status": "success", "message": f"Searched for {query}"}

@app.post("/send-whatsapp")
def send_whatsapp(contact_name: str, message: str):
    """
    Automates sending a WhatsApp message.
    Requires user to be logged in to WhatsApp Web in the chrome_profile.
    """
    global driver
    try:
        d = get_driver()
        d.get("https://web.whatsapp.com")
        
        wait = WebDriverWait(d, 30)
        
        # 1. Wait for Search Box (div with data-tab="3" is the search box)
        print("Waiting for WhatsApp to load...")
        search_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
        
        # 2. Search for contact
        print(f"Searching for {contact_name}...")
        search_box.click()
        search_box.clear()
        search_box.send_keys(contact_name)
        time.sleep(2) # Wait for results
        search_box.send_keys(Keys.ENTER)
        
        # 3. Wait for Chat to open (Message box has data-tab="10")
        print("Waiting for chat to open...")
        msg_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
        
        # 4. Type and Send
        print(f"Sending message: {message}")
        msg_box.click()
        msg_box.send_keys(message)
        time.sleep(0.5)
        msg_box.send_keys(Keys.ENTER)
        
        return {"status": "success", "message": f"Sent WhatsApp message to {contact_name}"}

    except Exception as e:
        print(f"WhatsApp Error: {e}")
        return {"status": "error", "message": f"Failed to send message: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
