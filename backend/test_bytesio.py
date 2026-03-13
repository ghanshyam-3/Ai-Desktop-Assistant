import io
import time
from gtts import gTTS
import pygame

print("Init mixer...")
pygame.mixer.init()
print("Generating TTS to memory...")
tts = gTTS("Testing Bytes I O streaming without physical files.")
fp = io.BytesIO()
tts.write_to_fp(fp)
fp.seek(0)

print("Loading into pygame...")
# Pygame 2+ requires specifying the extension hint if passing a file-like object for music
pygame.mixer.music.load(fp, "mp3")
print("Playing...")
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    time.sleep(0.1)

print("Done")
pygame.mixer.quit()
