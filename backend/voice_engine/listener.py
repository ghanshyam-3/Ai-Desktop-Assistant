import os
import numpy as np
import time # Added missing import
import openwakeword
from openwakeword.model import Model
from .capture import AudioCapture, CHUNK

# Ensure models are downloaded
openwakeword.utils.download_models()

class WakeWordListener:
    def __init__(self, callback):
        self.capture = AudioCapture()
        self.callback = callback
        # Load the model (using a default included model for now)
        self.owwModel = Model(wakeword_models=["hey_jarvis_v0.1"], inference_framework="onnx")
        self.is_listening = False
        self.paused = False

    def pause(self):
        self.paused = True
        print("Listener PAUSED")

    def resume(self):
        self.paused = False
        print("Listener RESUMED")

    def start(self):
        self.capture.start()
        self.is_listening = True
        print("Wake Word Engine Active. Waiting for 'hey jarvis'...")
        
        chunk_count = 0
        while self.is_listening:
            audio_bytes = self.capture.get_audio_chunk()
            if audio_bytes is None:
                continue

            if self.paused:
                # time.sleep(0.1) # removed
                continue # Discard audio to prevent buffer buildup

            chunk_count += 1
            if chunk_count % 50 == 0:
                print(".", end="", flush=True) # Heartbeat

            # Convert raw bytes to numpy array
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)

            # Bypass Wake Word: Trigger on Volume/Speech
            # Calculate volume (RMS) - Cast to float to avoid int16 overflow
            volume = np.sqrt(np.mean(audio_int16.astype(np.float32)**2))
            
            if volume > 500: # Simple volume threshold
                print(f"\nSpeech Detected (Vol: {volume:.0f})")
                if self.callback:
                    self.callback()
                    time.sleep(4) # Wait/Debounce so we don't trigger while recording
            
            # Wake Word Logic (DISABLED as per user request)
            # prediction = self.owwModel.predict(audio_int16)
            # for model_name, score in prediction.items():
            #    if score > 0.5: ...

    def stop(self):
        self.is_listening = False
        self.capture.stop()
