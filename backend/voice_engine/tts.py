import threading
import queue
import time
import os
import tempfile
from enum import Enum
import re
from gtts import gTTS
import pygame
from abc import ABC, abstractmethod

class SpeechState(Enum):
    IDLE = "IDLE"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"

class TextPreprocessor:
    @staticmethod
    def clean_text(text: str) -> str:
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        # Remove Markdown code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`.*?`', '', text)
        # Remove Markdown styling (bold, italic)
        text = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', text)
        text = re.sub(r'[#]+', '', text)
        # Remove Emojis (basic emoji range and extended) but KEEP useful unicode like quotes
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        # Clean up excess whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def chunk_sentences(text: str) -> list:
        # Split by basic punctuation
        chunks = re.split(r'(?<=[.!?]) +', text)
        return [c.strip() for c in chunks if c.strip()]

class TTSEngine(ABC):
    @abstractmethod
    def synthesize_and_play(self, chunk: str, stop_event: threading.Event, pause_event: threading.Event, volume: float) -> bool:
        pass
    
    @abstractmethod
    def stop(self):
        pass

class GTTS_Engine(TTSEngine):
    def synthesize_and_play(self, chunk: str, stop_event: threading.Event, pause_event: threading.Event, volume: float) -> bool:
        temp_file = ""
        try:
            # Generate secure temporary file path
            fd, temp_file = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            
            # Request translation with retry for API robustness
            for attempt in range(3):
                try:
                    tts = gTTS(text=chunk, lang='en', tld='com')
                    tts.save(temp_file)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise e
                    if stop_event.is_set():
                        return False
                    time.sleep(1)
            
            if stop_event.is_set():
                self._cleanup(temp_file)
                return False

            # Load and Play Audio
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                if stop_event.is_set():
                    pygame.mixer.music.stop()
                    self._cleanup(temp_file)
                    return False
                
                # Check for and handle pause state natively within engine
                if pause_event.is_set():
                    pygame.mixer.music.pause()
                    while pause_event.is_set() and not stop_event.is_set():
                        time.sleep(0.1)
                    if not stop_event.is_set():
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.stop()
                        self._cleanup(temp_file)
                        return False
                
                time.sleep(0.05)
                
            time.sleep(0.3) # Extended end buffer to prevent Pygame clipping mp3s
            pygame.mixer.music.unload()
            self._cleanup(temp_file)
            return True
            
        except Exception as e:
            print(f"GTTS play error: {e}")
            if temp_file:
                self._cleanup(temp_file)
            return False

    def stop(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    def _cleanup(self, temp_file):
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass

class Pyttsx3_Engine(TTSEngine):
    # Stub for offline pyttsx3 replacement avoiding COM constraints
    def synthesize_and_play(self, chunk: str, stop_event: threading.Event, pause_event: threading.Event, volume: float) -> bool:
        return False
        
    def stop(self):
        pass

class TTSHandler:
    def __init__(self):
        self.state = SpeechState.IDLE
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self.queue = queue.PriorityQueue()
        
        # Audio controls configuration
        self.volume = 1.0
        self.rate = 170
        self.enabled = True
        
        # Default engine mapping
        self.engine = GTTS_Engine()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        # Dedicated execution thread
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def set_engine(self, engine_name: str):
        if engine_name.lower() == "pyttsx3":
            self.engine = Pyttsx3_Engine()
        else:
            self.engine = GTTS_Engine()

    def _run_loop(self):
        """Dedicated thread for the TTS engine loop"""
        while True:
            try:
                # Blocks until an item is available
                priority, timestamp, text = self.queue.get()
                
                if not self.enabled:
                    self.queue.task_done()
                    continue

                self.state = SpeechState.PROCESSING
                self._stop_event.clear()
                self._pause_event.clear()
                
                cleaned_text = TextPreprocessor.clean_text(text)
                if not cleaned_text:
                    self.state = SpeechState.IDLE
                    self.queue.task_done()
                    continue

                chunks = TextPreprocessor.chunk_sentences(cleaned_text)
                self.state = SpeechState.SPEAKING
                
                for chunk in chunks:
                    if self._stop_event.is_set():
                        break
                    
                    if self._pause_event.is_set():
                        self.state = SpeechState.PAUSED
                        while self._pause_event.is_set() and not self._stop_event.is_set():
                            time.sleep(0.1)
                        if self.state == SpeechState.PAUSED and not self._stop_event.is_set():
                            self.state = SpeechState.SPEAKING

                    success = self.engine.synthesize_and_play(chunk, self._stop_event, self._pause_event, self.volume)
                    if not success and self._stop_event.is_set():
                        break # Stopped midway intentionally

                if self._stop_event.is_set():
                    self.state = SpeechState.STOPPED
                else:
                    self.state = SpeechState.IDLE
                    
                self.queue.task_done()
            
            except Exception as e:
                print(f"TTS Thread Error: {e}")
                self.state = SpeechState.IDLE

    def speak(self, text: str, priority: int = 1):
        """Non-blocking queue execution"""
        if not self.enabled:
            return
            
        if priority == 0:
            # High priority (e.g., system alert): stop current speech
            self.stop()
            
        self.queue.put((priority, time.time(), text))

    def stop(self):
        """Interrupt and clear current speech stream"""
        if self.state in [SpeechState.SPEAKING, SpeechState.PAUSED, SpeechState.PROCESSING]:
            print("TTS: Stopping...")
            self._stop_event.set()
            self._pause_event.clear()
            self.engine.stop()
            
            # Flush queue of standard priority messages
            with self.queue.mutex:
                self.queue.queue.clear()
            self.state = SpeechState.STOPPED

    def pause(self):
        if self.state == SpeechState.SPEAKING:
            self.state = SpeechState.PAUSED
            self._pause_event.set()

    def resume(self):
        if self.state == SpeechState.PAUSED:
            self._pause_event.clear()

    def set_volume(self, level: float):
        self.volume = max(0.0, min(1.0, level))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume)

    def toggle_speech(self, state: bool):
        self.enabled = state
        if not self.enabled:
            self.stop()

# Export Global Instance
tts_handler = TTSHandler()

def speak(text, priority=1):
    print(f"Assistant: {text}")
    tts_handler.speak(text, priority)

def stop_speaking():
    tts_handler.stop()

def is_speaking():
    return tts_handler.state in [SpeechState.SPEAKING, SpeechState.PROCESSING]
