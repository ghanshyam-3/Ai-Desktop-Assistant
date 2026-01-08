import subprocess
import time
import sys
import os
from dotenv import load_dotenv

def check_and_setup_env():
    """Checks for required env vars and prompts user if missing."""
    env_path = ".env"
    
    # Reload env to be sure
    load_dotenv(env_path)
    
    required_vars = {
        "GROQ_API_KEY": "Enter your Groq API Key (for LLM): ",
        "EMAIL_USER": "Enter your Email Address (Gmail): ",
        "EMAIL_PASSWORD": "Enter your Email App Password: ",
        "SMTP_SERVER": "Enter SMTP Server (default: smtp.gmail.com): ",
        "SMTP_PORT": "Enter SMTP Port (default: 587): "
    }
    
    defaults = {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587"
    }
    
    new_vars = {}
    updates_needed = False
    
    print("\n--- AI Assistant Setup ---")
    
    for var, prompt in required_vars.items():
        val = os.getenv(var)
        if not val:
            updates_needed = True
            user_val = input(prompt)
            if not user_val.strip() and var in defaults:
                user_val = defaults[var]
            new_vars[var] = user_val.strip()
    
    if updates_needed:
        print("\nSaving configuration to .env...")
        with open(env_path, "a") as f:
            f.write("\n")
            for key, value in new_vars.items():
                f.write(f'{key}="{value}"\n')
        # Reload again so current process has them
        load_dotenv(env_path, override=True)
        print("Configuration saved!\n")
    else:
        print("Configuration found. Starting up...\n")

def run_services():
    processes = []
    try:
        print("Starting System Service on port 8001...")
        p1 = subprocess.Popen([sys.executable, "services/system/main.py"], cwd=".")
        processes.append(p1)
        
        print("Starting Browser Service on port 8002...")
        p2 = subprocess.Popen([sys.executable, "services/browser/main.py"], cwd=".")
        processes.append(p2)

        print("Starting Email Service on port 8003...")
        p3 = subprocess.Popen([sys.executable, "services/email/main.py"], cwd=".")
        processes.append(p3)
        
        # Give them a moment to start
        time.sleep(2)
        
        print("Starting Orchestrator on port 8000...")
        # Orchestrator needs to be run as module to resolve relative imports if using "python -m orchestrator.main"
        # But here we wrote it as script. However, it imports ".llm", so it must be run as module or from package.
        # Let's run it as module.
        p3 = subprocess.Popen([sys.executable, "-m", "orchestrator.main"], cwd=".")
        processes.append(p3)
        
        print("\nAll services running. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all services...")
        for p in processes:
            p.terminate()
            
if __name__ == "__main__":
    check_and_setup_env()
    run_services()
