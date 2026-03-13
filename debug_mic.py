import pyaudio
import numpy as np
import time

def list_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    print("\n--- Available Audio Devices ---")
    input_devices = []
    for i in range(0, numdevices):
        device = p.get_device_info_by_host_api_device_index(0, i)
        if device.get('maxInputChannels') > 0:
            print(f"ID {i}: {device.get('name')}")
            input_devices.append(i)
    
    p.terminate()
    return input_devices

def test_recording(device_id=None):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    with open("mic_test_result.txt", "w") as log_file:
        def log(msg):
            print(msg)
            print(msg, file=log_file)
            log_file.flush()

        log(f"\n--- Testing Recording on Device ID: {device_id if device_id is not None else 'Default'} ---")
        log("Please speak into your microphone now (Recording for 3 seconds)...")
        
        try:
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            input_device_index=device_id,
                            frames_per_buffer=CHUNK)
    
            frames = []
            for i in range(0, int(RATE / CHUNK * 3)):
                data = stream.read(CHUNK)
                frames.append(np.frombuffer(data, dtype=np.int16))
                
            stream.stop_stream()
            stream.close()
            p.terminate()
    
            # Calculate Volume
            audio_data = np.hstack(frames)
            volume = np.max(np.abs(audio_data))
            log(f"Max Volume Detected: {volume}")
            
            if volume < 500:
                log("WARNING: Volume is very low. Microphone might be muted or not working.")
            else:
                log("SUCCESS: Audio detected!")
                
        except Exception as e:
            log(f"ERROR: {e}")

if __name__ == "__main__":
    ids = list_devices()
    if ids:
        # Test Default
        test_recording()
    else:
        print("No input devices found!")
    
    with open("mic_test_result.txt", "w") as f:
        print("Test Complete.", file=f)
