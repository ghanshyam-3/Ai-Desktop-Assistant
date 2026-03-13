# The AI Desktop Assistant: Complete internal Guide

This guide is designed to help you understand **exactly** how this project works so you can explain it to others or answer technical questions.

## 1. The Big Picture (Architecture)

Think of this application as a **digital brain** running on your computer. It has "Ears" (Microphone), a "Brain" (LLM), and "Hands" (Automation Tools).

```mermaid
graph TD
    User((User)) -->|Voice Command| Mic[Microphone Listener]
    Mic -->|Raw Audio| STT[Speech-to-Text (Whisper)]
    STT -->|Text| Brain[AI Logic (Llama 3)]
    
    Brain -->|Decision| ActionRouter{Action Router}
    
    ActionRouter -->|'open_app'| Launcher[App Launcher]
    ActionRouter -->|'web_search'| Browser[Web Browser]
    ActionRouter -->|'add_task'| DB[(Database)]
    ActionRouter -->|'analyze_screen'| Vision[Vision Model]
    
    Launcher --> Output[System Action]
    Browser --> Output
    DB -->|Update Dashboard| UI[Frontend UI]
    Vision -->|Description| TTS[Text-to-Speech]
    
    UI -->|Visual Feedback| User
    TTS -->|Audio Response| User
```

---

## 2. Core Modules & Libraries (The "Ingredients")

If someone asks **"What did you use to build this?"**, here is the answer:

### The Backend (Python) - *The Logic Center*
| Component | Library Used | Why we used it? |
| :--- | :--- | :--- |
| **API Server** | `FastAPI` | It's the fastest Python web framework. It handles the communication between the backend and frontend. |
| **Real-time Comms** | `python-socketio` | Allows the Backend to push updates (like "I'm listening") to the Frontend instantly without refreshing. |
| **AI Brain** | `Groq` | A customized API for running Llama 3 and Whisper. **Key advantage**: It is incredibly fast (near instant) compared to OpenAI. |
| **Database** | `SQLAlchemy` | Managing the local `tasks.db` file. It lets us treat database rows like Python objects. |
| **Hearing** | `PyAudio` & `NumPy` | `PyAudio` grabs raw sound data. `NumPy` does the math to check if the sound is loud enough (Speech Detection). |

### The Frontend (React) - *The Visual Interface*
| Component | Library Used | Why we used it? |
| :--- | :--- | :--- |
| **UI Framework** | `React` | Standard, component-based UI building. |
| **Visualizer** | `Canvas API` | We drew the "Particle Sphere" manually using code (Math + Physics) for high performance 60FPS animations. |
| **Styling** | `Tailwind CSS` | Rapid styling. Used for the "Glassmorphism" look (blur effects, transparency). |

---

## 3. Key Algorithms (The "Secret Sauce")

### A. How does it know when to listen? (VAD Algorithm)
**File**: `backend/voice_engine/listener.py`
Instead of constantly recording, we use a **Smart Silence Listener**:
1.  **Safety Buffer**: It constantly records small 30ms chunks of audio.
2.  **Volume Check**: It calculates the **RMS (Root Mean Square)**—basically the average loudness of the chunk.
3.  **Trigger**: If Loudness > Threshold, it starts saving the audio.
4.  **Cutoff**: If it detects silence for **2 seconds** after you stop talking, it assumes you are done and processes the audio.
*   **Why?**: This makes it feel natural. You don't need to press a button; you just speak.

### B. How does it understand intent? (The System Prompt)
**File**: `backend/server.py`
The AI doesn't "magically" know what to do. We send it a **System Prompt**—a hidden set of instructions that tells it:
> "You are a desktop assistant. If the user says 'Play music', output JSON like `{'action': 'open_app', 'target': 'Spotify'}`."

This separates the human language ("Can you open Spotify?") from the computer command (`open_app`).

---

## 4. Common Q&A (Be Ready to Answer!)

**Q: How does the AI navigate the screen?**
**A:** It currently uses a **Vision** capability (`analyze_screen`). It takes a screenshot, sends it to a Vision AI (Llama 3.2 Vision), and asks the AI to describe the coordinates or content of the screen.

**Q: Is my voice data sent to the cloud?**
**A:** Yes, but securely. The audio is sent to **Groq's API** for transcription (Whisper) and understanding (Llama). It is not processed locally (to keep your computer fast), but no data is stored permanently by the API.

**Q: How does the particle sphere work?**
**A:** It's a mathematical simulation. We create 400 "points" in 3D space (`x, y, z`).
*   **Idle**: They rotate slowly.
*   **Listening**: We boost the rotation speed and change color to Green.
*   **Speaking**: We add a `sine wave` to the radius `r`, causing the sphere to "pulse" like a heartbeat.

**Q: Why use Python AND Node.js/React?**
**A:**
*   **Python** is the best language for AI, Audio processing, and System automation.
*   **React** is the best for building beautiful, interactive UIs.
*   We bridge them using **Socket.IO**, giving us the best of both worlds.

**Q: What is the database schema?**
**A:** We use three main tables:
1.  **Tasks**: `id, title, status (pending/completed), due_date`
2.  **Notes**: `id, content, created_at`
3.  **Plans**: `id, title, progress_percentage`

---

## 5. Flow of a Feature: "Add a Task"

1.  **Microphone**: Hears "Remind me to buy eggs".
2.  **Backend**: `server.py` receives text "Remind me to buy eggs".
3.  **LLM**: Decides Action: `{'action': 'add_task', 'target': 'Buy eggs'}`.
4.  **Planner Module**: `planner.add_task("Buy eggs")` runs.
    *   It creates a `Task` object.
    *   It saves it to the SQLite database.
5.  **Signal**: Backend emits `socket.emit('dashboard_update', ...)`
6.  **Frontend**: React receives the event and updates the `tasks` state array.
7.  **Display**: The new task instantly pops up on the Dashboard screen without a refresh.
