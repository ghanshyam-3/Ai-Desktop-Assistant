
import sys
import os
import time
import threading

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

print("Importing server...")
try:
    from backend.server import AssistantState, set_state, current_state
    from backend.voice_engine.tts import tts_handler, speak, stop_speaking
    print("Imports successful.")
except Exception as e:
    print(f"Import Failed: {e}")
    sys.exit(1)

def test_tts_interrupt():
    print("\n[TEST] TTS Interruption")
    print("Speaking long text...")
    speak("This is a very long sentence that should be interrupted before it finishes because we are testing the stop functionality.")
    
    time.sleep(1)
    print("Calling STOP...")
    stop_speaking()
    
    time.sleep(0.5)
    if tts_handler.is_speaking:
        print("FAIL: Still speaking after stop.")
    else:
        print("PASS: Stopped successfully.")

def test_state_updates():
    print("\n[TEST] State Machine")
    set_state(AssistantState.PROCESSING)
    if current_state == AssistantState.PROCESSING:
        print("PASS: State updated to PROCESSING")
    else:
        print(f"FAIL: State is {current_state}")

if __name__ == "__main__":
    t = threading.Thread(target=test_tts_interrupt)
    t.start()
    t.join()
    
    test_state_updates()
    print("\nDone.")
