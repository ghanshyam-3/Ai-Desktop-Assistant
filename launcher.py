import webview
import threading
import sys
import os
import time
import uvicorn
from multiprocessing import Process # Pywebview needs to be main thread
from dotenv import load_dotenv

# Ensure proper path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check env Setup
from run_all import check_and_setup_env
check_and_setup_env()

# Import Service Apps
from services.system.main import app as system_app
from services.email.main import app as email_app
from services.browser.main import app as browser_app
from orchestrator.main import app as orchestrator_app

def run_service(app, port):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

def start_backend():
    print("Initializing Backend Services in Threads...")
    
    threads = []
    services = [
        (system_app, 8001),
        (browser_app, 8002),
        (email_app, 8003),
        (orchestrator_app, 8000)
    ]
    
    for app, port in services:
        t = threading.Thread(target=run_service, args=(app, port), daemon=True)
        t.start()
        threads.append(t)

if __name__ == '__main__':
    # Start Backend
    start_backend()
    
    # Wait for startup
    time.sleep(3)
    
    # Determine URL
    # If frozen, we rely on Orchestrator serving static files at port 8000
    if getattr(sys, 'frozen', False):
        url = 'http://localhost:8000'
    else:
        # Check if we should use Dev or Static
        # For "Current Project" user request, likely Dev if available, but for correctness of "launcher", 
        # let's default to Orchestrator (which falls back to serving dist if present)
        url = 'http://localhost:8000'

    print(f"Opening Desktop Window at {url}...")
    webview.create_window(
        title='AI Desktop Assistant', 
        url=url, 
        width=1200, 
        height=800,
        resizable=True,
        # frameless=True # User likes aesthetic, but let's keep frame for drag/close unless requested
    )
    
    webview.start()
    print("Exiting...")
    sys.exit()
