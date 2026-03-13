import time
from voice_engine.tts import TextPreprocessor, tts_handler

print("Testing Text Preprocessor:")
markdown_text = "Here is a **bold** response! Go to https://google.com for more info. `Code blocks` are removed! 😀"
cleaned = TextPreprocessor.clean_text(markdown_text)
print(f"Original: {markdown_text}")
print(f"Cleaned : {cleaned}")

print("\nTesting Priority Voice System:")
# Priority 1 (Normal)
tts_handler.speak("This is a normal paragraph, it will keep talking for a while.", priority=1)
time.sleep(2) # Let it speak for 2 seconds
print(f"State during speech: {tts_handler.state.name}")

# Priority 0 (Interrupt)
print("Interrupting with priority 0 alert!")
tts_handler.speak("Alert! This is a high priority interruption.", priority=0)

while tts_handler.state.name in ["SPEAKING", "PROCESSING"]:
    time.sleep(0.5)

print(f"Final State: {tts_handler.state.name}")
print("Test Complete")
