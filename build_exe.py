import PyInstaller.__main__
import os
import shutil

# Initial Setup
app_name = "AI_Desktop_Assistant"
entry_point = "launcher.py"

# Clean previous builds
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# Hidden imports required for Uvicorn/FastAPI/Engine
hidden_imports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.lifespan.on",
    "email.mime.multipart",
    "email.mime.text",
    "speech_recognition",
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",
    "comtypes",
    "comtypes.stream",
    # Add services modules manually if they aren't picked up by recursion
    "services.system.main",
    "services.email.main",
    "services.browser.main",
    "orchestrator.main",
    "orchestrator.core", 
    "orchestrator.audio",
    "orchestrator.llm"
]

# Build the command arguments
args = [
    entry_point,
    f'--name={app_name}',
    '--noconfirm',
    '--onefile',
    '--windowed', # Hide console
    # '--console', # Debug: Keep console open to see errors if any
    '--clean',
    
    # Data: Frontend Assets
    '--add-data=orchestrator/frontend/dist;frontend_dist',
    
    # Data: .env (User will likely need to provide this, or we bundle a default?)
    # Better: Don't bundle .env, let it be generated or read from local folder.
    # But for now, we leave it out of binary so it can be edited.
    
    # Imports
]

for imp in hidden_imports:
    args.append(f'--hidden-import={imp}')

# Run
print("Starting PyInstaller Build...")
PyInstaller.__main__.run(args)
print(f"Build Complete. Check dist/{app_name}.exe")
