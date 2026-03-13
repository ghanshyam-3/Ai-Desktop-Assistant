import pyaudio
import queue
import threading
import numpy as np

CHUNK = 1280
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

from .mic_utils import get_microphone_index

class AudioCapture:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.device_index = None

    def callback(self, in_data, frame_count, time_info, status):
        if self.is_running:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def start(self):
        self.is_running = True
        
        # Determine best device
        self.device_index = get_microphone_index()
        
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=CHUNK,
            stream_callback=self.callback
        )
        print("Microphone started Listening...")
        print("Microphone started Listening...")

    def stop(self):
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def get_audio_chunk(self):
        try:
            return self.audio_queue.get(timeout=0.5)
        except queue.Empty:
            return None
