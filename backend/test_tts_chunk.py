import time
from voice_engine.tts import speak, is_speaking

print("Testing chunked TTS")
speak("This is a very long sentence. It has multiple parts. Sometimes, it might get cut off if we don't handle it properly. But now, it should work perfectly because we are chunking it into smaller pieces. Let's see if it plays everything.")

time.sleep(2)
while is_speaking():
    time.sleep(1)

print("Done")
