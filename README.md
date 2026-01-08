# AI Desktop Assistant

A voice-activated AI Desktop Assistant that can control system applications, send emails, browse the web, and more.

## Prerequisites

- **Python** (3.10 or higher)
- **Node.js** (for building the frontend)

## Installation

1.  **Clone / Navigate to the project directory**:
    ```bash
    cd <project_directory>
    ```

2.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Frontend Dependencies**:
    ```bash
    cd orchestrator/frontend
    npm install
    cd ../..
    ```

## Configuration

The application requires API keys and credentials to function.
Run the launcher for the first time, and it will prompt you to enter them if missing:

- **Groq API Key**: For the LLM brain to process commands.
- **Email Credentials**: (Optional) Gmail address and App Password for sending emails.

These are saved in a `.env` file in the root directory.

## Running the Application

### Option 1: Desktop Application (Recommended)

This runs the backend services and opens the UI in a desktop window.

1.  **Build the Frontend** (Required once or after UI changes):
    ```bash
    cd orchestrator/frontend
    npm run build
    cd ../..
    ```

2.  **Run the Launcher**:
    ```bash
    python launcher.py
    ```

### Option 2: Development Mode

If you are modifying the code, you can run backend and frontend separately.

1.  **Start Backend Services**:
    ```bash
    python run_all.py
    ```

2.  **Start Frontend Dev Server** (in a new terminal):
    ```bash
    cd orchestrator/frontend
    npm run dev
    ```
    Then open `http://localhost:5173` in your browser.

## Features

- **Voice Commands**: Click the "Start" button or use wake words (if configured) to speak.
- **App Control**: "Open Notepad", "Open Calculator".
- **Web Browsing**: "Search Google for latest news", "Open YouTube".
- **Email**: "Send an email to [friend] saying [message]".
- **Visualizer**: Dynamic UI that responds to voice input.

## Troubleshooting

- **Audio Issues**: Ensure your microphone is set as the default system input.
- **Build Errors**: If `pywebview` fails, ensure you have the necessary system libraries installed.
