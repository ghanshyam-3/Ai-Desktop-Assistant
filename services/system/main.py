from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="System Control Service")

@app.get("/")
def home():
    return {"status": "System Service Running", "port": 8001}

import difflib

@app.post("/open-app")
def open_app(app_name: str):
    """
    Opens a system application.
    """
    print(f"Opening App: {app_name}")
    try:
        # Simple implementation for Windows
        # Known apps mapping for better launching
        known_apps = {
            "whatsapp": "start whatsapp:",
            "spotify": "start spotify:",
            "telegram": "start tg:",
            "settings": "start ms-settings:",
            "store": "start ms-windows-store:",
            "calculator": "calc",
            "notepad": "start notepad",
            "cmd": "start cmd",
            "chrome": "start chrome",
            "youtube": "start https://www.youtube.com",
            "facebook": "start https://www.facebook.com",
            "instagram": "start https://www.instagram.com",
            "google": "start https://www.google.com"
        }

        # Clean app name
        clean_name = app_name.lower().strip()
        
        # 1. Try known mapping
        if clean_name in known_apps:
            print(f"DEBUG: Opening known app '{clean_name}' via command")
            os.system(known_apps[clean_name])
            return {"status": "success", "message": f"Opened {clean_name}"}

        # 2. Try generic startfile (for files or exact exe names)
        print(f"DEBUG: Attempting to open '{app_name}' via startfile")
        try:
            os.startfile(app_name)
            return {"status": "success", "message": f"Opened '{app_name}'"}
        except FileNotFoundError:
            print(f"DEBUG: '{app_name}' not found locally.")
            
            # 3. SPELL CHECKER / SUGGESTION
            matches = difflib.get_close_matches(clean_name, known_apps.keys(), n=1, cutoff=0.6)
            if matches:
                 suggestion = matches[0]
                 return {
                     "status": "error", 
                     "message": f"App '{app_name}' not found. Did you mean '{suggestion}'?"
                 }

            # 4. Fallback: Open in Chrome
            print(f"DEBUG: Trying Chrome fallback for '{app_name}'")
            url = f"https://www.google.com/search?q={app_name}"
            os.system(f'start chrome "{url}"')
            return {"status": "success", "message": f"App not found. I searched for '{app_name}' in Chrome."}
            
        except Exception as e:
            return {"status": "error", "message": f"Error opening '{app_name}': {str(e)}"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

import pyautogui
import time

@app.post("/send-whatsapp")
def send_whatsapp(contact_name: str, message: str):
    """
    Sends a WhatsApp message using the Desktop Application via GUI Automation.
    """
    print(f"Sending WhatsApp to {contact_name}: {message}")
    try:
        # 1. Open WhatsApp
        os.system("start whatsapp:")
        time.sleep(3) # Wait for app to open/focus
        
        # 2. Search for Contact (Ctrl + F or just type if focused on list)
        # We assume startup focus is on chat list or search. 
        # Best bet: Ctrl+F to force search focus
        pyautogui.hotkey('ctrl', 'f') 
        time.sleep(0.5)
        
        # 3. Type Name and Enter
        pyautogui.write(contact_name)
        time.sleep(2.0) # Wait for search results (Increased)
        pyautogui.press('down') # Select first result
        time.sleep(0.5)
        pyautogui.press('enter') # Open chat
        time.sleep(2.0) # Wait for chat to load (Increased from 0.5s)
        
        # 4. Type Message and Send
        pyautogui.write(message)
        time.sleep(0.5)
        pyautogui.press('enter')
        
        return {"status": "success", "message": f"Sent message to {contact_name}"}

    except Exception as e:
        print(f"Automation Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
