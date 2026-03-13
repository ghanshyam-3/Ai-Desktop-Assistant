import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.getcwd())

# Mock EVERY dependency
modules_to_mock = [
    'voice_engine', 'voice_engine.listener', 'voice_engine.recognizer', 
    'voice_engine.mic_utils', 'voice_engine.capture', 'voice_engine.tts',
    'llm', 'llm.groq_client',
    'automation', 'automation.launcher', 'automation.browser', 
    'automation.email_sender', 'automation.system_control', 'automation.planner',
    'quotes', 'pyaudio', 'socketio', 'uvicorn', 
    'fastapi', 'fastapi.middleware.cors', 'dotenv', 'numpy', 'wave'
]

for m in modules_to_mock:
    sys.modules[m] = MagicMock()

print("Mocks setup. Importing server...")
try:
    import server
    print("Server imported successfully!")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
