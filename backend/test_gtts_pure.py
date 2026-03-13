import time
import os
from gtts import gTTS
import pygame

def test_audio():
    pygame.mixer.init()
    print("Generating audio...")
    tts = gTTS(text="Hello this is a test from the isolated script", lang='en')
    tts.save("test_output.mp3")
    
    print("Playing audio...")
    pygame.mixer.music.load("test_output.mp3")
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
        
    pygame.mixer.music.unload()
    os.remove("test_output.mp3")
    print("Done")

if __name__ == "__main__":
    test_audio()
