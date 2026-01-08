from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import sys
import os
from dotenv import load_dotenv
from .llm import parse_command
from .audio import speak
import threading
import time
import json
import asyncio

load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()
    print("DEBUG: Main Loop captured.")
    
    # Start the Assistant Core Loop
    from .core import core_loop
    # Inject dependencies to avoid circular import
    core_loop.set_dependencies(
        ui_update_cb=send_ui_update,
        ui_log_cb=send_ui_log,
        intent_exec_cb=execute_single_intent,
        ws_manager=manager
    )
    core_loop.start(main_loop)
    
    yield
    print("Shutting down...")
    core_loop.stop()

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Orchestrator Service", lifespan=lifespan)

# Allow CORS for React Frontend (Vite default port 5173) and local file opening
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost", "https://tauri.localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Frontend if built (Priority over root)
# Check if running in PyInstaller bundle
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    frontend_path = os.path.join(base_path, "frontend_dist")
else:
    # Check local dist
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend/dist")

if os.path.exists(frontend_path):
    print(f"Serving frontend from {frontend_path}")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

@app.get("/api/health")
def home():
    return {"message": "AI-assistant Orchestrator is running."}
BROWSER_SERVICE_URL = os.getenv("BROWSER_SERVICE_URL", "http://localhost:8002")
SYSTEM_SERVICE_URL = os.getenv("SYSTEM_SERVICE_URL", "http://localhost:8001")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8003")

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        print(f"DEBUG: Broadcasting to {len(self.active_connections)} clients: {message}")
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"DEBUG: Send failed: {e}")
                # self.disconnect(connection) # causing race condition?

manager = ConnectionManager()

# Async wrapper for broadcast to call from sync functions
def broadcast_sync(message: dict):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(manager.broadcast(message))
    loop.close()

# We need a thread-safe way to broadcast since listen loop is in a thread
# But asyncio loops in threads are tricky. 
# Better approach: The listen loop is sync. FastAPI is async.
# We will use a global queue or just fire-and-forget for now, 
# strictly speaking, "manager.broadcast" needs an event loop.
# Let's use a simple global reference to the main loop if possible, or use run_coroutine_threadsafe.

# Simplified for this context: We will rely on the fact that we can't easily await from the sync thread 
# without the loop. So we will make the listen loop async too? No, speech_recognition is blocking.
# Correction: We will use a global variable to store the loop and run_coroutine_threadsafe.

main_loop = None

def send_ui_update(state: str, message: str):
    print(f"UI UPDATE: {state} - {message}") # Debug
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "state", "state": state, "message": message}), 
            main_loop
        )

def send_ui_log(message: str, source: str = "system"):
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "log", "message": message, "source": source}), 
            main_loop
        )

def execute_single_intent(intent):
    """
    Executes a single workflow intent.
    """
    service = intent.get("service")
    action = intent.get("action")
    params = intent.get("params", {})
    
    print(f"Executing: Service={service}, Action={action}, Params={params}")

    if service == "conversational":
        response = intent.get("response", "I heard you.")
        send_ui_log(response, "system")
        send_ui_update("speaking", "Speaking...")
        speak(response)
        send_ui_update("idle", "Ready")

    elif service == "system":
        endpoint = ""
        if action == "open_app":
            endpoint = "/open-app"
            send_ui_update("processing", f"Opening {params.get('app_name')}...")
        elif action == "type_text":
            endpoint = "/type-text"
            send_ui_update("processing", f"Typing...")
        elif action == "send_whatsapp":
            endpoint = "/send-whatsapp"
            send_ui_update("processing", f"Messaging {params.get('contact_name')}...")

        if endpoint:
            try:
                # Add delay between actions for multi-step to be visible
                time.sleep(1) 
                resp = requests.post(f"{SYSTEM_SERVICE_URL}{endpoint}", params=params)
                data = resp.json()
                msg = data.get("message", "Task completed")
                send_ui_log(msg, "system")
                speak(msg)
            except Exception as e:
                send_ui_log(f"Error: {e}", "error")
                speak("I encountered an error executing that task.")
            send_ui_update("idle", "Done")

    elif service == "email":
        endpoint = ""
        if action == "send_email":
            endpoint = "/send-email"
            send_ui_update("processing", f"Sending email to {params.get('recipient')}...")

        if endpoint:
            try:
                # Add delay
                time.sleep(1)
                resp = requests.post(f"{EMAIL_SERVICE_URL}{endpoint}", json=params)
                print(f"DEBUG: Email Service returned {resp.status_code}")
                
                try:
                    data = resp.json()
                    msg = data.get("message", "Email sent")
                except:
                    msg = "Email sent (no json)"

                if resp.status_code == 200 and data.get("status") == "success":
                   send_ui_log(msg, "system")
                   speak("Email sent successfully.")
                else:
                   send_ui_log(f"Email Failed: {msg}", "error")
                   speak("Failed to send email.")
                
                send_ui_update("idle", "Done")
            except Exception as e:
                send_ui_log(f"Error: {e}", "error")
                speak("I couldn't reach the email service.")

    elif service == "browser":
        endpoint = ""
        if action == "open_url":
            endpoint = "/open-url"
        elif action == "search_google":
            endpoint = "/search"
            
        if endpoint:
            try:
                send_ui_update("processing", "Executing Browser Task...")
                resp = requests.post(f"{BROWSER_SERVICE_URL}{endpoint}", params=params)
                print(f"DEBUG: Browser Service returned {resp.status_code}")
                try:
                    data = resp.json()
                except Exception as json_err:
                    print(f"DEBUG: Failed to parse JSON. Raw response: {resp.text}")
                    raise json_err
                    
                msg = data.get("message", "Browser task completed")
                send_ui_log(msg, "system")
                send_ui_update("idle", "Done") 
                speak(msg)
            except Exception as e:
                send_ui_log(f"Error: {e}", "error")
                speak(f"Failed to communicate with Browser Service")

    elif service == "error":
        error_msg = intent.get("message", "Unknown Error")
        send_ui_log(f"Brain Error: {error_msg}", "error")
        send_ui_update("error", "Error")
        speak(f"I encountered an error: {error_msg}")

    else:
        send_ui_log(f"I didn't understand. Intent was: {service}", "error")
        speak("I did not understand which service to use.")
        send_ui_update("idle", "Ready")

def process_command(command_text: str):
    if not command_text:
        return

    send_ui_update("thinking", "Thinking...")
    send_ui_log(f"User said: {command_text}", "user")

    intent = parse_command(command_text)
    print(f"Intent: {intent}")
    
    if isinstance(intent, list):
        # Handle multiple commands
        for single_intent in intent:
            execute_single_intent(single_intent)
    else:
        # Handle single command
        execute_single_intent(intent)

from .core import core_loop

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"DEBUG: WS Received: {data}")
            
            if data == "start_listening":
                # Manual override: Force start listening?
                # For "Always On", this might mean "Listen NOW" (skip wake word)
                # But current frontend sends this on button click.
                # Ideally, we trigger the active listening state in core loop.
                send_ui_update("listening", "Listening (Manual)...")
                
                # We need to signal the core loop to switch state.
                # Since core loop is running in thread, we can just set state.
                core_loop.state = "LISTENING"

            elif data == "stop_listening":
                # Cancel current listening
                core_loop.recorder.stop()
                
            elif data.startswith("text_command:"):
                command_text = data.split("text_command:")[1]
                # Run processing in thread
                threading.Thread(target=process_command, args=(command_text,), daemon=True).start()
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)





if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
