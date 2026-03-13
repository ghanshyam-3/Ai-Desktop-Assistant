# 🤖 Nova AI – AI Desktop Assistant

> A voice-first, AI-powered desktop assistant built with **FastAPI**, **React**, and **Electron**. Talk to it, type to it — it controls your system, manages tasks, sends emails, searches the web, and more.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Voice Commands](#voice-commands)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Gmail Integration](#gmail-integration)
- [Known Limitations](#known-limitations)

---

## Overview

Nova AI is a **desktop assistant application** that runs locally on Windows. It combines:
- A **Python/FastAPI backend** that handles voice processing, intent recognition (via Groq LLM), and action execution
- A **React + Vite frontend** wrapped in **Electron** for a native desktop window
- **Real-time communication** via Socket.IO between frontend and backend
- A **local SQLite database** for tasks, notes, plans, email contacts, and message logs

---

## Features

| Category | Capability |
|----------|-----------|
| 🎙️ **Voice** | Wake-word detection, real-time speech-to-text (Google Speech API), TTS feedback |
| 🧠 **AI / LLM** | Intent classification via Groq (LLaMA 3), multi-turn conversation memory |
| 📋 **Task Manager** | Add, list, complete, delete tasks with priority, due dates, and tags |
| 📝 **Notes** | Create and list personal notes |
| 📅 **Planner** | Manage plans linked to tasks |
| 📧 **Email** | Send emails, check unread inbox, read email content (Gmail API) |
| 📬 **Email Contacts** | Save nicknames → email addresses for voice-driven email |
| 🖥️ **System Control** | Volume, mute, Wi-Fi, Bluetooth, hotspot, shutdown, restart, sleep, screenshot |
| 🌐 **Web Search** | Voice/text triggered web search in default browser |
| 📱 **App Launcher** | Open any installed app by name |
| 📸 **Screen Analysis** | Capture screen + ask LLM a question about it |
| 🎵 **Media** | Play songs/videos (pywhatkit + YouTube) |
| 📊 **Dashboard** | Visual overview of tasks by priority, status, date |
| 💬 **Chat** | General Q&A conversation fallback |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Electron Window                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              React + Vite Frontend                    │   │
│  │  App.jsx ─ Chat UI ─ Dashboard ─ Email Contacts       │   │
│  └──────────────┬────────────────────┬───────────────────┘   │
│                 │ Socket.IO          │ REST (fetch)           │
└─────────────────┼────────────────────┼───────────────────────┘
                  │                    │
┌─────────────────▼────────────────────▼───────────────────────┐
│                  FastAPI + Python-SocketIO                     │
│  server.py                                                    │
│  ├── Socket events: voice_command, text_command               │
│  ├── REST endpoints: /api/contacts, /api/email-logs           │
│  └── execute_action() ─ routes to modules below               │
│                                                               │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │  Groq    │ │  Voice   │ │  Planner    │ │   Gmail     │  │
│  │  LLM     │ │  Engine  │ │  (Tasks/   │ │  Service    │  │
│  │  Client  │ │          │ │  Notes)    │ │             │  │
│  └──────────┘ └──────────┘ └─────────────┘ └─────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐                   │
│  │  Browser │ │  System  │ │  App        │                   │
│  │ (Search) │ │ Control  │ │  Launcher   │                   │
│  └──────────┘ └──────────┘ └─────────────┘                   │
│                                                               │
│                    SQLite (SQLAlchemy)                        │
│       Tasks │ Notes │ Plans │ EmailContacts │ EmailLogs       │
└───────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Ai-app/
├── backend/                        # Python FastAPI backend
│   ├── server.py                   # Main app — Socket.IO, REST, execute_action()
│   ├── .env                        # Environment variables (API keys)
│   ├── requirements.txt            # Python dependencies
│   ├── credentials.json            # Google OAuth client credentials
│   ├── token.json                  # Gmail OAuth token (auto-generated)
│   ├── quotes.py                   # Motivational quotes module
│   │
│   ├── automation/                 # Action modules
│   │   ├── browser.py              # Web search
│   │   ├── launcher.py             # App opening (AppOpener)
│   │   ├── gmail_service.py        # Gmail send/read + contact management
│   │   ├── system_control.py       # Volume, Wi-Fi, Bluetooth, shutdown…
│   │   ├── planner.py              # Tasks, Notes, Plans (SQLAlchemy)
│   │   └── email_sender.py         # Legacy SMTP sender
│   │
│   ├── voice_engine/               # Voice input/output pipeline
│   │   ├── listener.py             # Microphone capture + speech recognition
│   │   ├── speaker.py              # TTS (pyttsx3) output
│   │   └── wake_word.py            # Wake-word detection (OpenWakeWord)
│   │
│   ├── llm/                        # LLM integration
│   │   └── groq_client.py          # Groq API wrapper (LLaMA 3)
│   │
│   ├── database/                   # Database layer
│   │   ├── db.py                   # SQLAlchemy engine + SessionLocal
│   │   └── models.py               # ORM models
│   │
│   └── scripts/
│       └── auth_gmail.py           # One-time Gmail OAuth script
│
├── frontend/                       # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx                 # Main app — layout, views, Socket.IO client
│   │   ├── pages/
│   │   │   ├── EmailContacts.jsx   # Email contact management UI
│   │   │   └── Dashboard.jsx       # Task analytics dashboard
│   │   ├── components/             # Reusable UI components
│   │   └── index.css               # Global styles
│   ├── package.json
│   └── vite.config.js
│
├── run_app.bat                     # Launcher: starts backend + frontend
└── build_backend.spec              # PyInstaller spec for production build
```

---

## Tech Stack

### Backend
| Library | Purpose |
|---------|---------|
| `FastAPI` | REST API + async server |
| `python-socketio` | Real-time frontend ↔ backend events |
| `Groq` | LLM intent classification (LLaMA 3.3 70B) |
| `SpeechRecognition` | Google Speech-to-Text |
| `pyttsx3` | Text-to-Speech (offline) |
| `openwakeword` | "Hey Nova" wake word detection |
| `pyaudio` | Microphone audio capture |
| `SQLAlchemy` | ORM + SQLite database |
| `google-api-python-client` | Gmail API integration |
| `AppOpener` | App launching by name |
| `psutil` | System info |
| `pyautogui` | Screenshot |
| `pywhatkit` | YouTube media playback |
| `python-dotenv` | `.env` file loading |

### Frontend
| Library | Purpose |
|---------|---------|
| `React 18` | UI framework |
| `Vite` | Dev server + bundler |
| `Electron` | Desktop window wrapper |
| `socket.io-client` | Real-time backend connection |
| `framer-motion` | Animations |
| `lucide-react` | Icons |
| `three.js` | 3D particle sphere visualizer |

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Windows OS (some features are Windows-specific)
- A [Groq API Key](https://console.groq.com)

### 1. Clone the repo
```bash
git clone <repo-url>
cd Ai-app
```

### 2. Backend setup
```bash
cd backend
pip install -r requirements.txt
```

### 3. Frontend setup
```bash
cd frontend
npm install
```

### 4. Configure environment
```bash
# Copy the example and fill in your values
# Edit backend/.env
```

---

## Environment Variables

File: `backend/.env`

```env
# ── AI Provider ──────────────────────────────────────────────
GROQ_API_KEY=your_groq_api_key_here

# ── Email (Gmail OAuth — set up via scripts/auth_gmail.py) ───
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=your_app_password       # Only used for SMTP fallback
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# ── App ──────────────────────────────────────────────────────
APP_ENV=development
```

> Get your Groq API key at [console.groq.com](https://console.groq.com) — it's free.

---

## Running the App

### Option A – One-click launcher
```bat
run_app.bat
```

### Option B – Manual (two terminals)
```bash
# Terminal 1 — Backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev       # or: npm run electron (for desktop window)
```

---

## Voice Commands

Activate by saying **"Hey Nova"** (wake word), then speak your command:

| Say... | Action |
|--------|--------|
| *"Open Chrome"* | Launches Google Chrome |
| *"Search for Python tutorials"* | Web search |
| *"What is the capital of France?"* | AI answer |
| *"Add task Buy groceries"* | Creates a task |
| *"List my tasks"* | Shows all tasks |
| *"Complete task Buy groceries"* | Marks task done |
| *"Delete task Buy groceries"* | Deletes task (asks confirmation) |
| *"Add note Call dentist tomorrow"* | Creates a note |
| *"Send email to Raj subject Hello body How are you?"* | Sends email |
| *"Check emails"* | Shows unread emails |
| *"Volume up / down"* | System volume |
| *"Take a screenshot"* | Captures screen |
| *"What's on my screen?"* | AI analyzes screen |
| *"Play Blinding Lights"* | Plays on YouTube |
| *"Shutdown / Restart / Sleep"* | System power (asks confirmation) |
| *"Show dashboard"* | Opens task dashboard |
| *"How are you?"* | General chat |

---

## API Reference

### Socket.IO Events

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `text_command` | Client → Server | `{ "text": "..." }` | Send a text command |
| `voice_command` | Client → Server | `{}` | Trigger voice listening |
| `assistant_response` | Server → Client | `{ "text": "...", "action": "..." }` | Assistant reply |
| `listening_state` | Server → Client | `{ "state": true/false }` | Mic on/off indicator |
| `voice_data` | Server → Client | audio data | TTS audio stream |

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/contacts` | List email contacts |
| `POST` | `/api/contacts` | Add email contact |
| `DELETE` | `/api/contacts/{id}` | Delete email contact |
| `GET` | `/api/email-logs` | Recent email send history |

---

## Database Schema

SQLite database auto-created at `backend/assistant.db`

```
Tasks          Notes          Plans
─────────      ──────         ──────
id             id             id
title          content        title
description    created_at     description
priority                      tasks (JSON)
status                        created_at
due_date
reminder_time
tags
completed_at
created_at

EmailContact   EmailLog
────────────   ────────
id             id
nickname       contact_id (FK)
email          recipient
created_at     subject
               status
               message_id
               error_message
               sent_at
```

---

## Gmail Integration

Gmail uses **OAuth 2.0** (not a password). One-time setup:

1. Place `credentials.json` from Google Cloud Console into `backend/`
2. Run:
   ```bash
   cd backend
   python scripts/auth_gmail.py
   ```
3. A browser opens → log in → grant permissions
4. `token.json` is saved — never need to do this again

> If the token ever expires, run `auth_gmail.py` again. The app starts normally even without a valid token (Gmail features are just disabled).

---

## Known Limitations

- 🪟 **Windows only** — some system control features use Windows APIs
- 🌐 **Internet required** — for Groq LLM, Gmail, Google Speech-to-Text
- 🎙️ **Microphone required** — for voice commands
- 🔇 **Quiet environment** — background noise can affect voice recognition accuracy
- 📧 **Gmail only** — currently no support for Outlook or other email providers
"# Ai-Desktop-Assistant" 
