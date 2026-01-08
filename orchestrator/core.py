import time
import threading
import json
import asyncio
from typing import Optional, Callable
import difflib

from .audio import speak, AudioRecorder
from .llm import parse_command
# Removed circular import: from .main import execute_single_intent, send_ui_update, send_ui_log, manager

# Wake word configuration
WAKE_WORDS = [
    "hyy gimi", "hey gimme", "hi gimme", "hey jimmy", "hi jimmy", "hey gimi", "high give me",
    "hey google", "hi google", "rajini", "genie", "hey genie", "jimmy"
]
WAKE_WORD_THRESHOLD = 0.8 # Confidence for difflib

class AssistantLoop:
    def __init__(self):
        self.running = False
        self.state = "IDLE" # IDLE, LISTENING, PROCESSING, SPEAKING
        self.thread: Optional[threading.Thread] = None
        self.recorder = AudioRecorder(volume_callback=self._volume_callback)
        self.loop_delay = 0.1
        self.main_loop: Optional[asyncio.AbstractEventLoop] = None
        self.should_follow_up = False
        
        # Dependencies injected at runtime
        self.ui_update_callback = None
        self.ui_log_callback = None
        self.intent_executor = None
        self.ws_manager = None
    
    def set_dependencies(self, ui_update_cb, ui_log_cb, intent_exec_cb, ws_manager):
        self.ui_update_callback = ui_update_cb
        self.ui_log_callback = ui_log_cb
        self.intent_executor = intent_exec_cb
        self.ws_manager = ws_manager

    def start(self, main_loop):
        """Starts the main assistant loop in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.main_loop = main_loop
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("Assistant Core Loop Started.")

    def stop(self):
        """Stops the loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("Assistant Core Loop Stopped.")

    def _volume_callback(self, amplitude):
        """Passes volume updates to the UI."""
        if int(time.time() * 100) % 4 != 0:
            return

        if self.main_loop and self.main_loop.is_running() and self.ws_manager:
             asyncio.run_coroutine_threadsafe(
                self.ws_manager.broadcast({"type": "volume", "level": float(amplitude)}), 
                self.main_loop
            )

    def _run_loop(self):
        """The main logic loop."""
        if self.ui_update_callback:
            self.ui_update_callback("idle", "Waiting for 'Hey Genie'...")

        while self.running:
            if self.state == "IDLE":
                self._handle_idle_state()
            
            elif self.state == "LISTENING":
                self._handle_active_listening()
                
            elif self.state == "FOLLOW_UP":
                # Same as listening but we might have a different UI state or log
                self._handle_active_listening()

            elif self.state == "PROCESSING":
                self.state = "IDLE"
            
            time.sleep(self.loop_delay)

    def _handle_idle_state(self):
        """
        Continuously listens for Wake Word.
        """
        # print("DEBUG: Listening for wake word...") 
        # Using a timeout to allow the loop to check self.running
        # But for wake word, we want to catch it even if said quickly.
        # phrase_time_limit=8 ensures we don't record forever if silence detection fails, but VAD should handle it.
        text = self.recorder.listen(timeout=2, phrase_time_limit=10)
        
        if not text:
            return 

        print(f"DEBUG: Heard in IDLE: {text}")
        
        is_wake, remainder = self._check_wake_word_and_extract(text)
        
        if is_wake:
            print(f"WAKE WORD DETECTED! Remainder: '{remainder}'")
            if self.ui_update_callback:
                 self.ui_update_callback("listening", "Listening...")

            # Check if there is already a command
            if remainder and len(remainder.strip()) > 3:
                print("DEBUG: Immediate command detected.")
                 # Process immediately
                self._process_text(remainder)
                # State transition handling is done in _process_text via should_follow_up
            else:
                # Wake word only. Enter Active Listening.
                speak("Yes?")
                self.state = "LISTENING"
        else:
            # Not a wake word, ignore.
            pass

    def _handle_active_listening(self):
        """
        Active command capture. Records until silence (VAD).
        """
        print("DEBUG: Active Listening...")
        if self.ui_update_callback:
             self.ui_update_callback("listening", "Listening...")
        
        # High phrase_time_limit allow long commands
        text = self.recorder.listen(timeout=5, phrase_time_limit=20)
        
        if not text:
            # If we were in follow up and heard nothing, maybe give up or ask one more time?
            # For now, return to IDLE
            if self.state == "FOLLOW_UP":
                 speak("I didn't hear a response.")
            
            self.state = "IDLE"
            if self.ui_update_callback:
                self.ui_update_callback("idle", "Waiting for 'Hey Genie'...")
            return

        self._process_text(text)

    def _process_text(self, text):
        """Helper to process a command text."""
        if self.ui_update_callback:
            self.ui_update_callback("thinking", "Thinking...")
        if self.ui_log_callback:
            self.ui_log_callback(f"User (Voice): {text}", "user")
        
        # Reset follow up flag
        self.should_follow_up = False
        
        self.state = "PROCESSING"
        try:
            intents = parse_command(text)
            
            # Check for follow up flag in intents
            if isinstance(intents, list):
                for intent in intents:
                    if intent.get("expect_reply", False):
                        self.should_follow_up = True
                        print("DEBUG: Intent requires follow-up.")
            elif isinstance(intents, dict):
                 if intents.get("expect_reply", False):
                        self.should_follow_up = True

            # Execute
            if self.intent_executor:
                if isinstance(intents, list):
                    for intent in intents:
                        self.intent_executor(intent)
                else:
                    self.intent_executor(intents)
            
            # Determine next state
            if self.should_follow_up:
                print("DEBUG: Switching to FOLLOW_UP state.")
                self.state = "FOLLOW_UP"
                # UI might stay "Listening" or "Thinking" -> "Listening"
                # The execution (speak) happens in intent_executor. 
                # After that, we want to be listening again.
            else:
                self.state = "IDLE"
                if self.ui_update_callback:
                    self.ui_update_callback("idle", "Waiting for 'Hey Genie'...")

        except Exception as e:
            if self.ui_log_callback:
                self.ui_log_callback(f"Error processing command: {e}", "error")
            speak("Sorry, I had trouble understanding that.")
            self.state = "IDLE"
            if self.ui_update_callback:
                self.ui_update_callback("idle", "Waiting for 'Hey Genie'...")

    def _check_wake_word_and_extract(self, text: str) -> tuple[bool, str]:
        """
        Checks for wake word. Returns (True, remainder_string) if found.
        """
        text_lower = text.lower().strip()
        
        # 1. Direct substring check
        for ww in WAKE_WORDS:
            if ww in text_lower:
                parts = text_lower.split(ww, 1)
                remainder = parts[1].strip() if len(parts) > 1 else ""
                return True, remainder
                
        # 2. Fuzzy check (difflib) for short phrases
        words = text.split()
        if not words: return False, ""
        
        # Check first 2-3 words
        candidate_phrase = " ".join(words[:3]).lower()
        
        for ww in WAKE_WORDS:
            ratio = difflib.SequenceMatcher(None, ww, candidate_phrase).ratio()
            if ratio >= WAKE_WORD_THRESHOLD:
                # Heuristic: assume whole text is relevant if it was short, 
                # or we effectively triggered. 
                # For fuzzy, hard to separate remainder cleanly without more logic.
                # Let's return empty remainder to force "Active Listening" phase, which is safer.
                return True, ""
        
        return False, ""

# Global instance
core_loop = AssistantLoop()
