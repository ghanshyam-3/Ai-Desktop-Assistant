import sounddevice as sd
import numpy as np
import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
import io
import scipy.io.wavfile as wav

# Initialize Speaker
engine = pyttsx3.init()
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 170)

def speak(text):
    """Speaks the given text."""
    print(f"Assistant: {text}")
    # engine.say(text) # Commented out to prevent blocking in some environments, uncomment if needed
    # engine.runAndWait()

# Audio Capture Configuration
SAMPLE_RATE = 16000
BLOCK_SIZE = 1024  # Size of audio chunks
CHANNELS = 1
SILENCE_THRESHOLD = 0.05  # Increased slightly to avoid background noise triggering too easily, but we will lower it if needed.
# Actually, sticking to a lower value is better for sensitivity. Let's keep it low but require consistent silence.
# Background noise in logs seems to be around 0.8 - 1.2
# Speech peaks are 40+.
# Setting threshold higher to prevent "Max Phrase Time" waits.
SILENCE_THRESHOLD = 3.0 
SILENCE_DURATION = 1.2    # Low latency response

# Global Queue for passing audio data
audio_queue = queue.Queue()

class AudioRecorder:
    def __init__(self, volume_callback=None):
        self.recording = False
        self.frames = []
        self.start_time = 0
        self.last_sound_time = 0
        self.stop_event = threading.Event()
        self.volume_callback = volume_callback

    def callback(self, indata, frames, time_info, status):
        """Callback for sounddevice. Captures audio and checks for silence."""
        if status:
            print(status)
        
        # Calculate Volume (RMS)
        amplitude = np.linalg.norm(indata) * 10
        
        # Trigger UI Visualizer
        if self.volume_callback:
            self.volume_callback(amplitude)
        
        # Determine if talking
        if amplitude > SILENCE_THRESHOLD:
            self.last_sound_time = time.time()
        
        # Store data
        self.frames.append(indata.copy())

        # Check for Silence Timeout
        if time.time() - self.last_sound_time > SILENCE_DURATION and len(self.frames) > (SAMPLE_RATE / BLOCK_SIZE):
            self.stop_event.set() # Signal to stop

    def stop(self):
        """Manually stop recording."""
        print("Manual Stop Triggered.")
        self.stop_event.set()

    def listen(self, timeout=None, phrase_time_limit=None):
        """
        Records audio until silence is detected.
        Returns the recognized text.
        """
        print(f"Listening (SoundDevice)... Timeout={timeout}")
        self.frames = []
        self.stop_event.clear()
        self.last_sound_time = time.time()
        
        start_recording_time = time.time()
        
        # Start Input Stream
        with sd.InputStream(callback=self.callback, 
                          channels=CHANNELS, 
                          samplerate=SAMPLE_RATE, 
                          blocksize=BLOCK_SIZE):
            
            # Wait until silence is detected or timeout
            while not self.stop_event.is_set():
                elapsed = time.time() - start_recording_time
                
                # Check for Timeout (waiting for speech to start)
                if timeout and elapsed > timeout and len(self.frames) < (SAMPLE_RATE / BLOCK_SIZE):
                    # Timeout reached without significant audio
                    print("Debug: Listen Timeout.")
                    return ""

                # Check for Phrase Time Limit (max duration of recording)
                if phrase_time_limit and elapsed > phrase_time_limit:
                    print("Debug: Max Phrase Time Reached.")
                    break
                
                time.sleep(0.1)
                
        print("Processing Audio...")
        
        if not self.frames:
            return ""

        # Convert frames to AudioData for SpeechRecognition
        audio_data = np.concatenate(self.frames, axis=0)
        
        # Scale to 16-bit integers
        audio_data_int = (audio_data * 32767).astype(np.int16)
        
        # Create Bytes Buffer
        byte_io = io.BytesIO()
        wav.write(byte_io, SAMPLE_RATE, audio_data_int)
        byte_data = byte_io.getvalue()
        
        # Use SpeechRecognition to process the WAV data
        r = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(byte_data)) as source:
            audio = r.record(source)
            try:
                command = r.recognize_google(audio)
                print(f"User: {command}")
                return command
            except sr.UnknownValueError:
                print("Debug: Audio not understood.")
                return ""
            except sr.RequestError as e:
                print(f"Debug: Request Error; {e}")
                return ""
