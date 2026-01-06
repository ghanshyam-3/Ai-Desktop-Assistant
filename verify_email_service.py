import requests
import time
import subprocess
import sys
import os

def test_email_service():
    # Start the service
    print("Starting Email Service...")
    proc = subprocess.Popen([sys.executable, "services/email/main.py"], cwd=".")
    
    try:
        time.sleep(3) # Wait for startup
        
        url = "http://localhost:8003/send-email"
        payload = {
            "recipient": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email from the verification script."
        }
        
        print(f"Sending request to {url}...")
        try:
            resp = requests.post(url, json=payload, timeout=5)
            print(f"Status Code: {resp.status_code}")
            print(f"Response: {resp.json()}")
            
            if resp.status_code == 200:
                print("SUCCESS: Service is reachable and responded.")
            else:
                print("FAILURE: Service returned error.")
                
        except Exception as e:
            print(f"FAILURE: Request failed: {e}")

    finally:
        print("Stopping service...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    # Check if .env has credentials
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("EMAIL_USER"):
        print("WARNING: EMAIL_USER not set in .env. Integration test will likely fail authentication but verify reachability.")
    
    test_email_service()
