import os
import uvicorn
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

from voice_engine.listener import WakeWordListener
from voice_engine.recognizer import CommandRecognizer
from voice_engine.mic_utils import get_microphone_index
from voice_engine.capture import AudioCapture
from voice_engine.tts import speak, stop_speaking, is_speaking
from llm.groq_client import GroqClient
from automation.launcher import AppLauncher
from automation.browser import Browser
from automation.gmail_service import GmailService
from automation.system_control import SystemControl
from automation.planner import Planner
import threading
import json
import asyncio
import uuid
import datetime
import pywhatkit # Added missing import
import webbrowser
import os
import pyaudio # Added missing import
import numpy as np
import traceback


# Initialize FastAPI
app = FastAPI(title="Voice Desktop Assistant")

# Allow CORS (for Frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# Initialize Modules
groq_client = GroqClient()
launcher = AppLauncher()
browser = Browser()
gmail = GmailService()
sys_control = SystemControl()
planner = Planner()

# Global State
listener = None
main_loop = None
chat_history = [] # Context Window
is_voice_active = True # Global Mute Flag
is_typing = False # Typing Flag

def update_listener_state():
    """
    Centralized logic to determine if listener should be active.
    Listener accepts audio ONLY if:
    1. Global Voice is ACTIVE (not muted manually)
    2. User is NOT typing
    """
    global listener, is_voice_active, is_typing
    if not listener: return

    if is_voice_active and not is_typing:
        if listener.paused:
             listener.resume()
    else:
        if not listener.paused:
             listener.pause()

# State Machine
class AssistantState:
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    CONFIRMATION = "confirmation"

current_state = AssistantState.IDLE
pending_action = None # Check for pending confirmations

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    start_voice_listener()

def set_state(state):
    global current_state
    current_state = state
    print(f"State -> {state}")

def notify_frontend(state, text):
    """Emits event to frontend"""
    if main_loop and sio:
        asyncio.run_coroutine_threadsafe(
            sio.emit('status', {'state': state, 'text': text}), 
            main_loop
        )

def notify_chat(role, text):
    """Emits chat message to frontend"""
    if main_loop and sio:
        print(f"Chat Event: {role} -> {text}")
        asyncio.run_coroutine_threadsafe(
            sio.emit('chat', {'role': role, 'message': text}), 
            main_loop
        )

@app.post("/api/contacts")
async def add_email_contact(contact: dict):
    nickname = contact.get('nickname')
    email = contact.get('email')
    if not nickname or not email: return {"error": "Missing fields"}
    success, msg = gmail.add_contact(nickname, email)
    return {"success": success, "message": msg}

@app.get("/api/contacts")
async def get_email_contacts():
    return gmail.get_contacts()

@app.delete("/api/contacts/{id}")
async def delete_email_contact(id: int):
    success, msg = gmail.delete_contact(id)
    return {"success": success, "message": msg}

@sio.event
async def text_command(sid, data):
    """Handle text input from frontend"""
    text = data.get('text')
    print(f"Received Text Command: {text}")
    # Run in thread to not block async loop
    threading.Thread(target=process_command, args=(text,)).start()

def process_command(text_input=None, continuous_mode=False):
    """
    Main Logic: Record (or use text) -> Understand -> Act
    """
    global current_state, chat_history, is_voice_active, pending_action
    
    # Check Global Mute Flag (CRITICAL FIX)
    if not text_input and not is_voice_active:
        print("Voice is MUTED. Ignoring process_command.")
        if continuous_mode:
             set_state(AssistantState.IDLE)
        return

    # If already processing, ignore (unless it's a barge-in handling which calls this fresh)
    if current_state == AssistantState.PROCESSING: 
        return

    # HANDLE CONFIRMATION STATE
    if current_state == AssistantState.CONFIRMATION:
        print(f"In Confirmation State. Input: {text_input}")
        # We need to capture the user's YES/NO response here.
        # Use the provided text_input or listen if None.
        
        user_response = ""
        if text_input:
            user_response = text_input.lower().strip()
        else:
            # We are in confirmation state, but this function was called probably from a wake word or just a loop.
            # We need to listen for the confirmation.
            
            # PAUSE GLOBAL LISTENER TO AVOID CONTENTION
            if listener: listener.pause()
            
            rec = CommandRecognizer()
            audio = rec.listen_for_command()
            
            # RESUME GLOBAL LISTENER
            if listener: listener.resume()
            
            if audio:
                user_response = groq_client.transcribe("confirmation.wav", prompt="yes, no, cancel, confirm, do it") # We can reuse temp file logic properly or just string
                if os.path.exists("confirmation.wav"):
                    os.remove("confirmation.wav")
            else:
                user_response = ""

        # Analyze Response
        if user_response in ["yes", "yeah", "yep", "do it", "sure", "confirm", "okay"]:
            if pending_action:
                print(f"Action CONFIRMED: {pending_action}")
                action = pending_action['action']
                target = pending_action['target']
                pending_action = None
                set_state(AssistantState.PROCESSING)
                # Proceed to execution below (we skip the LLM part and go to execution)
                feedback = execute_action(action, target) # Refactored execution
                finish_interaction(feedback)
                return
        elif user_response in ["no", "nope", "cancel", "stop", "don't"]:
            print("Action CANCELLED.")
            pending_action = None
            speak("Cancelled.")
            set_state(AssistantState.IDLE)
            return
        else:
            # Ambiguous response to confirmation -> Treat as new command?
            # Or just say "I didn't understand, cancelling."
            # For robustness, let's treat it as a potential new command if it's long, 
            # but if it's short and ambiguous, just cancel.
            print(f"Ambiguous confirmation response: {user_response}")
            pending_action = None
            speak("I didn't catch a confirmation, so I cancelled that.")
            set_state(AssistantState.IDLE)
            return

    set_state(AssistantState.PROCESSING)

    user_text = ""
    temp_file = None # Initialize temp_file here for finally block access

    try:
        if text_input:
            # Case 1: Text Input
            user_text = text_input
            notify_frontend(AssistantState.PROCESSING, f"cmd: {user_text}")
            notify_chat('user', user_text)
        else:
            # Case 2: Voice Input
            notify_frontend(AssistantState.LISTENING, 'Listening...')
            
            print("Recording command... (CommandRecognizer)")
            
            # PAUSE GLOBAL LISTENER TO AVOID CONTENTION
            if listener: listener.pause()
            
            rec = CommandRecognizer()
            
            # Only adjust noise once or if specifically requested, to save time in continuous mode
            # rec.adjust_noise() 
            
            audio = rec.listen_for_command()
            
            # RESUME GLOBAL LISTENER
            if listener: listener.resume()
            
            if not audio:
                 if continuous_mode:
                     # In continuous mode, silence means user is done
                     print("Continuous mode: Silence detected. returning to IDLE.")
                 else:
                     notify_frontend(AssistantState.IDLE, 'Could not hear you.')
                 
                 set_state(AssistantState.IDLE)
                 return

            # Save temp file with UNIQUE name to avoid PermissionError
            temp_file = f"command_{uuid.uuid4().hex}.wav"
            
            with open(temp_file, "wb") as f:
                f.write(audio.get_wav_data())
        
            # 3. Notify: Processing
            notify_frontend(AssistantState.PROCESSING, 'Thinking...')
            
            # 4. Transcribe
            biasing_prompt = "start, stop, help, open, search, answer, email, volume, mute, wifi, bluetooth, shutdown, restart, sleep, screenshot, timer, alarm, reminder, note, task, dashboard, new chat, reset, yes, no, confirm, cancel"
            
            try:
                user_text = groq_client.transcribe(temp_file, prompt=biasing_prompt)
            except Exception as e:
                print(f"Transcription error: {e}")
                user_text = ""
            
            print(f"User said: {user_text}")
            
            # Cleanup with error handling
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except PermissionError:
                    print(f"Warning: Could not delete temp file {temp_file} (PermissionError). It may be in use.")
                except Exception as e:
                    print(f"Warning: Could not delete temp file {temp_file}: {e}")

            # --- garbage Filter ---
            # Ignore empty, very short, or hallucinated text
            if not user_text or len(user_text.strip()) < 2:
                print("Ignoring short/empty transcription.")
                if continuous_mode:
                    set_state(AssistantState.IDLE)
                else:
                     notify_frontend(AssistantState.IDLE, 'Could not hear you.')
                return

            ignored_phrases = ["thank you", "you're welcome", "mbc news", "copyright", "amara.org", "uncredited"]
            if user_text.lower().strip() in ignored_phrases:
                 print("Ignoring known hallucination.")
                 set_state(AssistantState.IDLE)
                 return
            # ----------------------
        
            notify_frontend(AssistantState.PROCESSING, f"cmd: {user_text}")
            notify_chat('user', user_text)

        # --- STOP COMMAND INTERCEPTION ---
        if user_text.lower().strip() in ["stop", "stop speaking", "shut up", "cancel"]:

            stop_speaking()
            notify_frontend(AssistantState.IDLE, 'Stopped.')
            set_state(AssistantState.IDLE)
            return
            
        # --- NEW CHAT COMMAND INTERCEPTION ---
        if user_text.lower().strip() in ["new chat", "start over", "reset chat", "forget everything"]:
            chat_history = []
            feedback = "Okay, I've cleared the chat history. Starting fresh."
            notify_chat('ai', feedback)
            
            set_state(AssistantState.SPEAKING)
            notify_frontend(AssistantState.SPEAKING, feedback)
            
            speak(feedback)
            
            time.sleep(1) # Wait a bit
            set_state(AssistantState.IDLE)
            return

        # 5. Understand (LLM)
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        system_prompt = f"""
        Act as Desktop Assistant. Time: {current_time}, Date: {current_date}
        Return JSON: {{ 'action': string, 'target': any, 'confidence': 'high'|'medium'|'low' }}
        IMPORTANT: If command matches an action, confidence MUST be 'high'. Only use 'low' for complete gibberish.
        
        Actions:
        1. 'open_app': Target=App name
        2. 'web_search': Target=Query
        3. 'answer': Target=Answer text
        4. 'send_email': Target={{'to': string, 'subject': string, 'body': string}}. Important: If the user provides a short description of what to email, YOU MUST generate a professional, complete email 'subject' and 'body' based on their request. Missing 'to' info -> return 'chat'.
        5. 'check_email': Target=null
        6. 'read_email': Target=null
        7. 'system_control': Target in ['volume_up', 'volume_down', 'mute', 'wifi_on', 'wifi_off', 'bluetooth_on', 'bluetooth_off', 'hotspot', 'shutdown', 'restart', 'sleep', 'screenshot']
        8. 'analyze_screen': Target=User Question. ONLY if user asks to see screen.
        9. 'add_task': Target=Description
        10. 'list_tasks': Target=null
        11. 'add_note': Target=Content
        12. 'list_notes': Target=null
        13. 'complete_task': Target=Task Name
        14. 'delete_task': Target=Task Name
        15. 'show_dashboard': Target=null
        16. 'reset_conversation': Target=null
        17. 'chat': Target=Reply (Use for greetings, 'how are you', or general questions not covered above).
        18. 'play_media': Target=Song Name / Video Title (e.g. "Blinding Lights", "Python tutorial").

        Examples:
        "Open Chrome" -> {{ "action": "open_app", "target": "Google Chrome", "confidence": "high" }}
        "Play Blinding Lights" -> {{ "action": "play_media", "target": "Blinding Lights", "confidence": "high" }}
        "Emails?" -> {{ "action": "check_email", "target": null, "confidence": "high" }}
        "How are you?" -> {{ "action": "chat", "target": "I'm doing well, thank you!", "confidence": "high" }}
        "Hello" -> {{ "action": "chat", "target": "Hello there!", "confidence": "high" }}
        "Email John to schedule a meeting tomorrow" -> {{ "action": "send_email", "target": {{"to": "John", "subject": "Meeting Request: Tomorrow", "body": "Hi John,\\n\\nI would like to schedule a meeting with you for tomorrow. Please let me know what time works best for you.\\n\\nBest regards,"}}, "confidence": "high" }}
        "asdf vb" -> {{ "action": null, "target": null, "confidence": "low" }}

        """
        
        # Update History
        chat_history.append({"role": "user", "content": user_text})
        
        # Keep Memory Small (Last 10 turns)
        if len(chat_history) > 10:
            chat_history.pop(0)

        # Call LLM with History
        intent_json_str = groq_client.process_intent(chat_history, system_prompt)
        try:
            intent = json.loads(intent_json_str)
            action = intent.get('action')
            target = intent.get('target')
            confidence = intent.get('confidence', 'medium') # Default to medium if missing
        except:
            action = None
            target = None
            confidence = 'low'
            
        print(f"Intent classified: Action={action}, Confidence={confidence}")

        # --- CONFIRMATION LOGIC ---
        CRITICAL_ACTIONS = ['delete_task', 'shutdown', 'restart', 'sleep', 'send_email']
        
        # 1. Handle Null Action (Fallback to Chat)
        if action is None:
             print("Action is None. Fallback to CHAT.")
             # Fallback logic: Treat as chat/answer
             # We can't easily get the "answer" if LLM didn't give it to us.
             # But if we have the user_text, we can try a separate chat call or just say "I heard {user_text}"
             
             # Better approach: If action is None, use a lightweight chat completion
             conversation_reply = groq_client.get_chat_completion(chat_history, system_prompt="You are a helpful assistant. Reply to the user.")
             feedback = conversation_reply
             
             # Update state to IDLE after speaking
             notify_chat('ai', feedback)
             speak(feedback)
             set_state(AssistantState.IDLE)
             return

        # 2. Ignore Low Confidence - DISABLED to improve responsiveness
        # if confidence == 'low' and action != 'chat':
        #      print("Confidence Low. Speaking fallback.")
        #      notify_frontend(AssistantState.IDLE, 'Not sure.')
        #      speak("I didn't quite catch that.")
        #      return

        # 3. Confirmation Check - DISABLED AS PER USER REQUEST
        needs_confirmation = False
        
        # if action in CRITICAL_ACTIONS:
        #     needs_confirmation = True
        # elif confidence == 'low' and action != 'chat':
        #      # Should be caught above, but redundancy is fine
        #     needs_confirmation = True
            
        if needs_confirmation:
            pending_action = {'action': action, 'target': target}
            set_state(AssistantState.CONFIRMATION)
            
            confirm_msg = f"I heard you say you want to {format_action_for_speech(action, target)}. Is that right?"
            notify_frontend(AssistantState.CONFIRMATION, "Confirm?")
            speak(confirm_msg)
            return

        # 6. Execute & Speak (Immediate Execution)
        feedback = execute_action(action, target)
        finish_interaction(feedback)

    except Exception as e:
        print(f"CRITICAL ERROR in process_command: {e}")
        traceback.print_exc()
        notify_frontend(AssistantState.IDLE, "Error occurred.")
        speak("I encountered an error.")
    finally:
        # ALWAYS clean up state if we are not in confirmation or speaking
        # If we are in CONFIRMATION, we wait for user.
        # If we are SPEAKING, finish_interaction handles it.
        # But if we crashed or finished normally without state change, force IDLE.
        if current_state == AssistantState.PROCESSING:
             set_state(AssistantState.IDLE)


def format_action_for_speech(action, target):
    if action == 'delete_task': return f"delete the task {target}"
    if action == 'send_email': return "send an email"
    if action == 'shutdown': return "shut down the computer"
    return "do that"

def finish_interaction(feedback):
    global current_state
    should_speak = True
    
    if start_speaking(feedback):
        # Continuous mode trigger logic can go here if needed
        # For now, just reset to IDLE after speaking
        pass

def start_speaking(feedback):
    if not feedback: return False
    
    set_state(AssistantState.SPEAKING)
    notify_frontend(AssistantState.SPEAKING, feedback)
    notify_chat('ai', feedback)
    

    speak(feedback)
    
    # Wait until speaking is done OR interrupted
    while is_speaking():
        time.sleep(0.1)
        if current_state != AssistantState.SPEAKING:
            return False
    
    current_state = AssistantState.IDLE
    return True

def execute_action(action, target):
    feedback = ""
    
    if action == 'open_app':
        success, msg = launcher.open_app(target)
        if not success:
            browser.smart_open(target)
            feedback = f"Could not find {target} app, so I opened it in browser."
        else:
            feedback = msg
    elif action == 'web_search':
        feedback = browser.search(target)
    elif action == 'answer':
        feedback = target
    elif action == 'send_email':
        if isinstance(target, dict):
            to_field = target.get('to')
            subject = target.get('subject', 'No Subject')
            body = target.get('body', '')
            
            # Resolve Nickname
            if '@' not in to_field:
                resolved_email = gmail.get_email_by_nickname(to_field)
                if resolved_email:
                    to_field = resolved_email
                else:
                    return f"I couldn't find an email for contact '{to_field}'."

            success, msg = gmail.send_email(to_field, subject, body)
            feedback = msg
        else:
            feedback = "I couldn't extract the email details."

    elif action == 'check_email':
        emails = gmail.check_unread_emails()
        if isinstance(emails, list):
            if not emails:
                feedback = "You have no new unread emails."
            else:
                feedback = f"**You have {len(emails)} unread emails:**\n\n"
                for i, email in enumerate(emails, 1):
                    sender_name = email['sender'].split('<')[0].strip().replace('"', '')
                    feedback += f"**{i}. {sender_name}**\n   _{email['subject']}_\n\n"
        else:
            feedback = emails # Error string

    elif action == 'read_email':
        # For now, same logic. Later: filter
        emails = gmail.check_unread_emails() 
        if isinstance(emails, list):
            if not emails:
                feedback = "No unread emails to read."
            else:
                feedback = "**Here are your emails:**\n\n"
                for i, email in enumerate(emails, 1):
                    sender_name = email['sender'].split('<')[0].strip().replace('"', '')
                    snippet = email['snippet'][:150] + "..." if len(email['snippet']) > 150 else email['snippet']
                    
                    feedback += f"**{i}. From:** {sender_name}\n"
                    feedback += f"**Subject:** {email['subject']}\n"
                    feedback += f"_{snippet}_\n"
                    feedback += "---\n"
        else:
            feedback = emails

    elif action == 'play_media':
        song = target
        feedback = f"Playing {song} on YouTube..."
        try:
            import pywhatkit
            pywhatkit.playonyt(song)
        except Exception as e:
            print(f"PyWhatKit Error: {e}")
            # Fallback to simple web search if pywhatkit fails
            import webbrowser
            webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
            feedback = f"Searching for {song} on YouTube (Driver Error)."

    elif action == 'system_control':
        feedback = sys_control.execute(target)
    elif action == 'analyze_screen':
        notify_frontend(AssistantState.PROCESSING, 'looking at screen...')
        screenshot_path = sys_control.take_screenshot()
        feedback = groq_client.analyze_image(target, screenshot_path)
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)     
    elif action == 'add_task':
        feedback = planner.add_task(target)
        notify_dashboard_update()
    elif action == 'list_tasks':
        feedback = planner.list_tasks()
    elif action == 'complete_task':
        if planner.complete_task_by_name(target):
            feedback = f"Marked '{target}' as completed."
            notify_dashboard_update()
        else:
            feedback = f"I couldn't find a pending task called '{target}'."
    elif action == 'delete_task':
        if planner.delete_task_by_name(target):
            feedback = f"Deleted task '{target}'."
            notify_dashboard_update()
        else:
            feedback = f"I couldn't find a task called '{target}'."
    elif action == 'show_dashboard':
        if main_loop and sio:
            asyncio.run_coroutine_threadsafe(
                sio.emit('navigate', 'dashboard'),
                main_loop
            )
        feedback = "Opening dashboard."
    
    elif action == 'add_note':
        feedback = planner.add_note(target)
        notify_dashboard_update()
    elif action == 'list_notes':
        feedback = planner.list_notes()
    elif action == 'reset_conversation':
        # Handled earlier but good to have
        feedback = "Chat history cleared."
        
    elif action == 'get_good_thought':
        from quotes import get_random_quote
        feedback = get_random_quote()
    elif action == 'chat':
        feedback = target
    else:
        # Fallback to general chat
        # If we reached here with action='chat' or unknown
        # The prompt might return action='answer' for chat now, 
        # so this might be Less reached.
        # But if action was None, we returned early.
        # If action was 'chat' (hypothetically), we just return target.
        if target:
            feedback = target
        else:
            feedback = "I'm listening."

    # Update history for assistant
    chat_history.append({"role": "assistant", "content": feedback})
    return feedback




def wake_word_callback():
    """Callback when wake word is detected OR Barge-in triggers"""
    global current_state, is_voice_active, is_typing
    
    # safeguard against race conditions
    if not is_voice_active:
        print("Wake word detected but Voice is MUTED. Ignoring.")
        return

    if is_typing:
        print("Wake word detected but User is TYPING. Ignoring.")
        return
        
    print(f"Wake Word/Barge-in Triggered! State: {current_state}")
    
    if current_state == AssistantState.SPEAKING:
        print("Interruption detected! Stopping TTS...")

        stop_speaking()
        
    # Start processing (which begins with recording)
    threading.Thread(target=process_command, args=(None, False)).start()

def start_voice_listener():
    global listener
    listener = WakeWordListener(callback=wake_word_callback)
    thread = threading.Thread(target=listener.start, daemon=True)
    thread.start()

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Voice assistant backend"}

@sio.event
async def connect(sid, environ):
    global current_state, is_voice_active
    print(f"Client connected: {sid}")
    
    # Reset State on Reload
    current_state = AssistantState.IDLE
    is_voice_active = True # Always start fresh as Unmuted
    update_listener_state()
    
    await sio.emit('status', {'text': 'System Ready', 'state': 'idle'})

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def start_typing(sid):
    """Pause listener when user is typing"""
    global is_typing
    is_typing = True
    print(f"User typing... Pausing listener.")
    update_listener_state()

@sio.event
async def stop_typing(sid):
    """Resume listener when user stops typing"""
    global is_typing
    is_typing = False
    print(f"User stopped typing. Checking listener state...")
    update_listener_state()

@sio.event
async def toggle_listening(sid, data):
    """Manually toggle voice listener"""
    global is_voice_active
    active = data.get('active')
    is_voice_active = active
    print(f"Manual Voice Toggle: {'ON' if active else 'OFF'}")
    
    update_listener_state()

@sio.event
async def fetch_dashboard(sid):
    """Send current tasks, notes, and plans to client"""
    tasks = planner.get_tasks()
    notes = planner.get_notes()
    plans = planner.get_plans()
    await sio.emit('dashboard_update', {'tasks': tasks, 'notes': notes, 'plans': plans})

@sio.event
async def add_item_manual(sid, data):
    """Handle manual UI addition of Task, Note, or Plan"""
    type = data.get('type') # 'task' or 'note' or 'plan'
    content = data.get('content') # String or Dict
    date_str = data.get('date') # ISO string YYYY-MM-DD
    
    if type == 'task':
        # Content might be a dict now {title, priority} or just string "title"
        title = content
        priority = "medium"
        
        if isinstance(content, dict):
            title = content.get('title')
            priority = content.get('priority', 'medium')
            
        import datetime
        final_date = None
        if date_str:
            try:
                final_date = datetime.datetime.fromisoformat(date_str)
            except:
                pass
        planner.add_task(title=title, priority=priority, due_date=final_date)
        
    elif type == 'note':
        # Content might be dict {content}
        note_text = content
        if isinstance(content, dict):
            note_text = content.get('content')
        planner.add_note(note_text)
        
    elif type == 'plan':
        # Content might be dict {title}
        plan_title = content
        if isinstance(content, dict):
            plan_title = content.get('title')
        planner.add_plan(title=plan_title)
        
    # Broadcast update
    tasks = planner.get_tasks()
    notes = planner.get_notes()
    plans = planner.get_plans()
    
    await sio.emit('dashboard_update', {'tasks': tasks, 'notes': notes, 'plans': plans})

@sio.event
async def update_item(sid, data):
    """Handle item updates (e.g. checkbox toggle)"""
    type = data.get('type')
    id = data.get('id')
    updates = data.get('updates') # dict of changes e.g. {'status': 'completed'}
    
    if type == 'task':
        if 'status' in updates:
            planner.complete_task(id, status=updates['status'])
            
    # Broadcast update
    tasks = planner.get_tasks()
    notes = planner.get_notes()
    plans = planner.get_plans()
    await sio.emit('dashboard_update', {'tasks': tasks, 'notes': notes, 'plans': plans})

def notify_dashboard_update():
    """Helper to broadcast dashboard state"""
    if main_loop and sio:
        tasks = planner.get_tasks()
        notes = planner.get_notes()
        asyncio.run_coroutine_threadsafe(
            sio.emit('dashboard_update', {'tasks': tasks, 'notes': notes}),
            main_loop
        )

def start_server():
    """Entry point for direct execution"""
    uvicorn.run("server:socket_app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
