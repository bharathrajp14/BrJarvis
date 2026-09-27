# BR JARVIS — Manual Setup, Configuration & Operations Guide
**Canonical Operating Manual for BR JARVIS MK40.2 (Mark XL.2)**  
*Document Version:* `40.2.0` | *Updated:* `2026-08-15`

---

## 📋 Table of Contents
1. [Quick Start Checklist](#1-quick-start-checklist)
2. [Runtime & OS Prerequisites](#2-runtime--os-prerequisites)
3. [API Keys & LLM Backend Provisioning](#3-api-keys--llm-backend-provisioning)
4. [Audio & Voice Hardware Setup](#4-audio--voice-hardware-setup)
5. [Server Security & Web UI Authentication](#5-server-security--web-ui-authentication)
6. [App Connectors & External Service Integrations](#6-app-connectors--external-service-integrations)
7. [Operating Modes & Launch Commands](#7-operating-modes--launch-commands)
8. [Permission Policies & OS Safety](#8-permission-policies--os-safety)
9. [Mobile Companion & Remote Access](#9-mobile-companion--remote-access)
10. [Memory, Vector Database & Artifact Storage](#10-memory-vector-database--artifact-storage)
11. [Troubleshooting & Maintenance Runbooks](#11-troubleshooting--maintenance-runbooks)

---

## 1. Quick Start Checklist

| Step | Action | Command / Location | Status |
| :--- | :--- | :--- | :--- |
| **1** | Verify Python 3.10 – 3.12 64-bit | `python --version` | Required |
| **2** | Install dependencies | `pip install -e .` or `pip install -r requirements.txt` | Required |
| **3** | Copy environment file | `cp .env.template .env` | Required |
| **4** | Provide Primary LLM Key | Add `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env` | Required |
| **5** | Set Server API Key | Set `SERVER_API_KEY` in `.env` (Default: `23DA981E`) | Required |
| **6** | Run Smoke Verification | `python scripts/smoke_startup.py` | Recommended |
| **7** | Launch Web / CLI / Voice | `python start.py web` or `python start.py cli` | Ready |

---

## 2. Runtime & OS Prerequisites

### 2.1 Python Version
- **Supported Versions**: Python 3.10, 3.11, 3.12 (64-bit).
- **Python 3.14 Alpha Note**: `start.py` contains automated detection that gracefully re-routes from Python 3.14 pre-release to your system's stable Python 3.12 installation.
- **Virtual Environment Setup (Recommended)**:
  ```powershell
  # Windows PowerShell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install --upgrade pip setuptools wheel
  pip install -e .
  ```

### 2.2 System Utilities & Native Binaries
1. **FFmpeg (Required for Speech Recognition & Audio Processing)**:
   - *Windows (winget)*: `winget install Gyan.FFmpeg`
   - *Windows (Chocolatey)*: `choco install ffmpeg`
   - *Manual*: Download from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) and add the `bin` folder to your system `PATH`.
   - *Verification*: Open terminal and run `ffmpeg -version`.
2. **C++ Build Tools (Required if compiling PyAudio or C extensions)**:
   - Install "Desktop development with C++" from [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
   - Alternatively, install pre-compiled PyAudio wheels: `pip install pipwin; pipwin install pyaudio`.

---

## 3. API Keys & LLM Backend Provisioning

BR JARVIS supports multiple LLM providers with automatic fallback to local models. Open your `.env` file to configure your preferred backend.

### 3.1 Primary Cloud Providers

```ini
# Google Gemini (Primary & Fastest Multi-Modal Engine)
GEMINI_API_KEY="AIzaSyYourKeyHere..."
GEMINI_LISTEN_API_KEY="AIzaSyYourKeyHere..."

# OpenAI / OpenAI-Compatible Proxies
OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL="https://api.openai.com/v1" # Or http://localhost:8045/v1
OPENAI_MODEL="gemini-3.6-flash-high"

# Anthropic Claude
ANTHROPIC_API_KEY="sk-ant-..."
JARVIS_MODEL_CLAUDE="claude-sonnet-4-6"

# DeepSeek / Groq / Mistral / NVIDIA (Optional)
DEEPSEEK_API_KEY="sk-..."
GROQ_API_KEY="gsk_..."
NVIDIA_API_KEY="nvapi-..."
MISTRAL_API_KEY="..."
```

### 3.2 100% Offline LLM with Ollama

If running in air-gapped or offline mode without cloud API keys:
1. Download and install [Ollama](https://ollama.com/).
2. Pull your desired models:
   ```bash
   ollama pull llama3.3
   ollama pull qwen2.5-coder:7b
   ollama pull nomic-embed-text
   ```
3. Set in `.env`:
   ```ini
   OLLAMA_HOST=http://127.0.0.1:11434
   OLLAMA_DEFAULT_MODEL=llama3.3
   JARVIS_DEFAULT_BACKEND=ollama
   JARVIS_FORCE_OFFLINE=true
   ```

---

## 4. Audio & Voice Hardware Setup

### 4.1 Windows Microphone Permissions
1. Open **Windows Settings** -> **Privacy & Security** -> **Microphone**.
2. Ensure **"Microphone access"** is switched **ON**.
3. Ensure **"Let desktop apps access your microphone"** is switched **ON**.

### 4.2 Selecting Audio Devices
If you have multiple microphones (e.g., Headset, USB Yeti, Webcam):
1. Run the device discovery tool:
   ```bash
   python -c "import sounddevice as sd; print(sd.query_devices())"
   ```
2. Note the device index and add to `.env`:
   ```ini
   JARVIS_AUDIO_INPUT_DEVICE="Microphone (Yeti Classic)"
   JARVIS_AUDIO_OUTPUT_DEVICE="Speakers (Realtek Audio)"
   ```

### 4.3 Acoustic Threshold Tuning
In `.env`:
```ini
JARVIS_ASSISTANT_NAME="BR Jarvis"
JARVIS_WAKE_WORD="hey jarvis"
JARVIS_AUDIO_MIN_RMS=0.015       # Minimum audio volume to trigger speech detection (0.010 - 0.030)
JARVIS_ENABLE_BARGE_IN=true      # Allows interrupting JARVIS while speaking
JARVIS_WHISPER_MODEL="base.en"   # Options: tiny.en, base.en, small.en, medium.en
```

---

## 5. Server Security & Web UI Authentication

BR JARVIS enforces token and session-based authentication to protect local and network execution.

### 5.1 Setting the Server API Key
In `.env` or `config/api_keys.json`:
```ini
SERVER_API_KEY=23DA981E
```

### 5.2 Authenticating in the Web Dashboard
1. Start the server: `python start.py web`.
2. Open `http://127.0.0.1:8000` in Chrome/Edge/Firefox.
3. When the **🔐 Server Authentication** modal appears:
   - Enter your key: `23DA981E`
   - Click **AUTHENTICATE**.
4. The key is securely stored in `localStorage` and a session cookie is issued. The real-time telemetry stream and WebSocket channels will immediately connect.

---

## 6. App Connectors & External Service Integrations

Enable external connectors by adding their credentials into `.env`:

### 6.1 GitHub Connector
- **Purpose**: Manage repositories, create PRs, trigger GitHub Actions, inspect issues.
- **Setup**: Create a Personal Access Token (Classic or Fine-grained) at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo`, `workflow`, and `read:org` scopes.
- **Config**: `GITHUB_TOKEN="ghp_YourGitHubTokenHere..."`

### 6.2 Telegram Bot Connector
- **Purpose**: Receive alerts, chat with JARVIS via Telegram, approve destructive tasks remotely.
- **Setup**:
  1. Message `@BotFather` on Telegram to create a new bot and obtain your Bot Token.
  2. Message your new bot, then message `@userinfobot` to find your Telegram Chat ID.
- **Config**:
  ```ini
  TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
  TELEGRAM_ALLOWED_USERS="YourNumericChatId"
  ```

### 6.3 Gmail & Google Workspace Connector
- **Purpose**: Draft emails, summarize inboxes, search calendar events.
- **Setup**:
  1. Enable 2-Step Verification on your Google Account.
  2. Generate an **App Password** at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
- **Config**:
  ```ini
  GMAIL_ADDRESS="youremail@gmail.com"
  GMAIL_APP_PASSWORD="abcd efgh ijkl mnop"
  ```

### 6.4 Web Search (Tavily Engine)
- **Purpose**: Real-time internet search and autonomous research.
- **Setup**: Free API key at [tavily.com](https://tavily.com/).
- **Config**: `TAVILY_API_KEY="tvly-..."`

---

## 7. Operating Modes & Launch Commands

BR JARVIS provides 4 primary operational entry points via `start.py`:

```bash
# 1. Web Operating System Dashboard (Recommended)
# Launches FastAPI backend + Cyberpunk Glassmorphic UI on http://127.0.0.1:8000
python start.py web

# 2. Interactive Terminal CLI
# Full agent loop with streaming output, slash commands (/mode, /tasks), and rich banners
python start.py cli

# 3. Voice Assistant & Wake-Word HUD
# Full real-time microphone listening, wake-word activation ("Hey Jarvis"), and TTS feedback
python start.py voice

# 4. Headless Core Server (Docker / Background Service)
python start.py api
```

---

## 8. Permission Policies & OS Safety

JARVIS includes a safety gate to control OS-level side effects (file modifications, shell commands, registry changes).

### Permission Modes (`JARVIS_PERMISSION_MODE`)
Configured in `.env`:
- `allow_all` *(Development default)*: Executes tools and terminal commands autonomously.
- `confirm_destructive` *(Production recommended)*: Prompts for confirmation before deleting files, executing system-level scripts, or modifying sensitive configurations.
- `confirm_all`: Prompts before every tool execution.
- `deny_all`: Read-only mode.

### Safe Artifacts Directory
By default, all user-facing generated documents (PDF, DOCX, XLSX, charts) are safely exported to:
```
%USERPROFILE%\Documents\BR-JARVIS\artifacts\
```
Override this in `.env`: `JARVIS_ARTIFACTS_DIR="D:/MyExports"`

---

## 9. Mobile Companion & Remote Access

### 9.1 Local Network Pairing
1. Ensure your mobile device is connected to the same Wi-Fi network.
2. In the Web UI, navigate to the **📱 Mobile** tab.
3. Scan the generated QR code or open `http://<YOUR_PC_LAN_IP>:8000/mobile`.

### 9.2 Secure Remote Tunneling (Tailscale / Cloudflare)
To access JARVIS securely from outside your home network without exposing open router ports:
- **Tailscale (Recommended)**: Install Tailscale on your host PC and phone; access JARVIS at `http://<your-tailscale-ip>:8000`.
- **Cloudflare Tunnel**:
  ```bash
  cloudflared tunnel --url http://127.0.0.1:8000
  ```

---

## 10. Memory, Vector Database & Artifact Storage

### Directory Layout
```
d:\BRJARVIS\Br-Jarvis\
├── workspace/          # Working scratchpad for autonomous sub-agents
├── memory_db/           # ChromaDB / SQLite persistent RAG vectors & conversation logs
├── audit.log           # Tamper-evident ledger of all tool executions
├── config/             # System configuration & connector credentials
└── web/                # Glassmorphic Web App shell & PWA assets
```

### Manual Maintenance Actions
- **Resetting Memory**: If you want to purge past conversational memory and re-index clean documentation:
  ```powershell
  Remove-Item -Recurse -Force ./memory_db/*
  ```
- **Clearing Orphaned Sub-Agent Locks**:
  ```powershell
  python -c "from agent.recovery_watchdog import get_recovery_watchdog; get_recovery_watchdog().inspect_and_recover()"
  ```

---

## 11. Troubleshooting & Maintenance Runbooks

### Runbook 1: Browser Shows Cached Old Version / 401 Loops
- **Symptom**: Web console shows older script version or reconnects in a loop.
- **Fix**:
  1. Perform a hard refresh: Press `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac).
  2. The built-in cache-buster script in `index.html` will automatically unregister older Service Workers and purge legacy cache.
  3. Click **🔑 AUTH** in the top-right header and submit your `SERVER_API_KEY` (`23DA981E`).

### Runbook 2: Port 8000 Already in Use
- **Symptom**: `ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`
- **Fix**:
  1. JARVIS automatically detects port conflicts and shifts to the next available port (`8001`, `8002`, etc.).
  2. To release port 8000 manually on Windows:
     ```powershell
     netstat -ano | findstr :8000
     taskkill /PID <PID_NUMBER> /F
     ```

### Runbook 3: Microphone Not Detecting Audio
- **Symptom**: Voice engine stays on `LISTENING` without transcribing speech.
- **Fix**:
  1. Verify microphone permissions in Windows Settings.
  2. Test RMS sensitivity: Lower `JARVIS_AUDIO_MIN_RMS=0.008` in `.env`.
  3. Ensure `ffmpeg` is available on PATH: `Get-Command ffmpeg`.

### Runbook 4: Full System Self-Verification
To run the automated verification suite covering all unit tests and end-to-end control loops:
```powershell
pytest tests/unit/ tests/e2e/ -v
```
*(All 18 production test suites should pass with 100% success rate).*
