import speech_recognition as sr
import time

class CommandRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def adjust_noise(self):
        """
        Calibrates the recognizer for ambient noise.
        """
        print("Adjusting for ambient noise... (1s)")
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Noise adjustment complete.")

    def listen_for_command(self):
        """
        Listens for a voice command with specific silence constraints.
        Returns: sr.AudioData
        """
        # Energy Threshold Configuration
        # Start with a less sensitive threshold to ignore background murmurs
        self.recognizer.energy_threshold = 400 
        self.recognizer.dynamic_energy_threshold = False
        
        # Turn-Taking Logic (Silence Constraints)
        self.recognizer.pause_threshold = 0.5  # Wait 500ms (Reduced from 800ms) for faster response
        self.recognizer.non_speaking_duration = 0.25 # Start recording after 250ms of silence
        
        print(f"Listening... (Threshold: {self.recognizer.energy_threshold})")
        
        with sr.Microphone() as source:
            try:
                # Listen with a timeout to prevent hanging forever if no speech
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                return audio
            except sr.WaitTimeoutError:
                print("Listening timed out (no speech detected).")
                return None
