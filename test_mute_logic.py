
import sys
import os
import threading
import time

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

print("Importing server...")
try:
    import backend.server as server
    from backend.server import process_command, AssistantState, set_state
    print("Imports successful.")
except Exception as e:
    print(f"Import Failed: {e}")
    sys.exit(1)

def test_mute_logic():
    print("\n[TEST] Mute Logic")
    
    # 1. Test Process Command while MUTED
    print("Simulating Mute...")
    server.is_voice_active = False
    
    print("Calling process_command(continuous_mode=True)...")
    # This should return immediately and NOT block or change state to LISTENING
    start_time = time.time()
    process_command(continuous_mode=True)
    duration = time.time() - start_time
    
    if duration < 0.1 and server.current_state != AssistantState.LISTENING:
        print("PASS: process_command ignored call while muted.")
    else:
        print(f"FAIL: process_command took {duration}s or changed state to {server.current_state}")

    # 2. Test Wake Word Callback while MUTED
    print("\n[TEST] Wake Word Callback Mute")
    server.current_state = AssistantState.IDLE
    server.wake_word_callback() # Should print mismatch message and return
    
    # Needs manual verification of print output, but state shouldn't change
    if server.current_state == AssistantState.IDLE:
        print("PASS: Wake word callback ignored trigger while muted.")
    else:
         print(f"FAIL: Wake word changed state to {server.current_state}")

if __name__ == "__main__":
    test_mute_logic()
