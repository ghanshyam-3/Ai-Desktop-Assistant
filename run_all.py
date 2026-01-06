import subprocess
import time
import sys

def run_services():
    processes = []
    try:
        print("Starting System Service on port 8001...")
        p1 = subprocess.Popen([sys.executable, "services/system/main.py"], cwd=".")
        processes.append(p1)
        
        print("Starting Browser Service on port 8002...")
        p2 = subprocess.Popen([sys.executable, "services/browser/main.py"], cwd=".")
        processes.append(p2)
        
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
    run_services()
