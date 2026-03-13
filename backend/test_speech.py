import time
from voice_engine.tts import speak, is_speaking, stop_speaking
print("Speaking starting...")
speak("Hello world, this is a test to see if audio is working.")
time.sleep(1)
print(f"Is speaking: {is_speaking()}")
time.sleep(5)
print("Finished test")
