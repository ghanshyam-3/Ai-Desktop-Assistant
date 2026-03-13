@echo off
echo Starting Voice Assistant AI...

:: Start Backend
start "Voice Assistant Backend" cmd /k "cd backend && python server.py"

:: Wait a moment for backend to initialize
timeout /t 3

:: Start Frontend (Electron + React)
cd frontend
echo Starting Frontend...
cmd /k "npm run electron:dev"
