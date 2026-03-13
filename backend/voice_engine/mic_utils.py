import pyaudio

def get_microphone_index():
    """
    Finds the index of the best available microphone.
    Prioritizes devices with 'microphone' in the name.
    """
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    best_index = None
    best_name = ""
    
    print(f"--- Scanning Audio Devices ({numdevices}) ---")
    for i in range(0, numdevices):
        d = p.get_device_info_by_host_api_device_index(0, i)
        if d.get('maxInputChannels') > 0:
            name = d.get('name')
            print(f"ID {i}: {name}")
            
            # Heuristic: Prefer "Microphone" over others
            if "microphone" in name.lower() and best_index is None:
                best_index = i
                best_name = name
            
            # Heuristic: Prefer USB devices if multiple
            if "usb" in name.lower() and "microphone" in name.lower():
                best_index = i
                best_name = name
                
    p.terminate()
    
    if best_index is not None:
        print(f"Selected Microphone: ID {best_index} ({best_name})")
        return best_index
    else:
        print("No specific microphone found. Using Default.")
        return None
