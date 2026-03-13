import pyaudio
import audioop
import time

def list_microphones():
    p = pyaudio.PyAudio()
    print("--- Available Audio Devices ---")
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    input_devices = []
    
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            name = p.get_device_info_by_host_api_device_index(0, i).get('name')
            print(f"Device {i}: {name}")
            input_devices.append(i)
            
    print("-------------------------------")
    
    # Test recording from default device
    try:
        print("\nTesting Default Input Device (Index None)...")
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=1024)
        
        print("Listening for 5 seconds... PLEASE SPEAK NOW.")
        
        max_rms = 0
        min_rms = 99999
        
        for _ in range(0, int(16000 / 1024 * 5)):
            data = stream.read(1024, exception_on_overflow=False)
            rms = audioop.rms(data, 2)
            if rms > max_rms: max_rms = rms
            if rms < min_rms: min_rms = rms
            # print(f"RMS: {rms}", end='\r')
            
        print(f"\nStats: Max RMS={max_rms}, Min RMS={min_rms}")
        
        if max_rms < 100:
            print("WARNING: Input is extremely quiet. Check microphone mute/volume.")
        elif max_rms < 300:
            print("WARNING: Input is very quiet.")
        else:
            print("SUCCESS: Audio detected.")
            
        stream.stop_stream()
        stream.close()
    except Exception as e:
        print(f"Error testing default device: {e}")
        
    p.terminate()

if __name__ == "__main__":
    list_microphones()
