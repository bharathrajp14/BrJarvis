# JARVIS MK38 — Full Project Documentation

> [!NOTE]
> **Complete Master Reference Available**: For exhaustive directory analyses across all 43 folder domains, 2,021 project files, 905,930 LOC, security remediation reports, and architecture diagrams, refer to [PROJECT_MASTER_DOCUMENTATION.md](file:///d:/BRJARVIS/Br-Jarvis/PROJECT_MASTER_DOCUMENTATION.md) and the audit database [BR_JARVIS_Developer_Audit_Updated.xlsx](file:///d:/BRJARVIS/Br-Jarvis/BR_JARVIS_Developer_Audit_Updated.xlsx).

## Overview
**JARVIS MK38** is an advanced, multi-modal, and multi-backend AI assistant platform. It operates as both a voice-powered interactive assistant and a high-performance command-line orchestrator. The platform allows for dynamic switching between multiple LLM backends and utilizes an intelligent routing engine to match specific tasks to the most capable configured model. 

The system is engineered for **Cross-Platform Compatibility** (Windows, Linux, macOS), ensuring robust fallback mechanisms for OS-specific capabilities.

---

## 1. Core Architecture

The system is built on a modular, decoupled architecture prioritizing stability and extensibility.

### 1.1 Multi-Backend Foundation
The platform does not rely on a single AI provider. Instead, it maintains unified interfaces for:
- **`anthropic_backend.py`**: Interacts with Claude models (optimizes for coding/security).
- **`gemini_backend.py`**: Interacts with Google's Gemini models (optimizes for search/long context, vision).
- **`openai_backend.py`**: Interacts with GPT models (optimizes for creative tasks).
- **`ollama_backend.py`**: Enables fully 100% local, offline, privacy-first inference.
- **`nvidia_backend.py`**: Hooks into NVIDIA NIM endpoints for accelerated GPU-bound inference.
- **`mistral_backend.py`**: Utilizes Mistral AI models, excellent for rapid inference and multilingual text processing.

### 1.2 Routing Engine (`router.py`)
JARVIS uses a keyword-based ReAct routing engine to intelligently dispatch requests to the best available backend. 
- **Configuration Hierarchy**: The router automatically sets the fallback `default_backend` by checking Environment variables, `config/models.json`, and hardcoded defaults.
- **Graceful Degradation**: If the preferred model for a task is missing an API key or offline, the router seamlessly falls back to the default configured backend.

### 1.3 Dual Launch Interfaces
Users can interact with the AI through two independent interfaces, bridged through `start.py` or the `startup.bat` executable:
- **Voice Interface (`main.py`)**: Uses local audio transcription and ElevenLabs/system TTS for spoken interactions. Features natively injected vision capabilities (`screen_process`).
- **CLI Orchestrator (`main_mk37.py`)**: A professional, rich-text command-line terminal optimized for DevSecOps, offering explicit slash commands (`/skills`, `/memory`, `/install-skills`).

---

## 2. The Skills & Tools Ecosystem

JARVIS combines 47 deterministic Python tools with a dynamic "Skill" ecosystem representing repeatable prompt templates.

### 2.1 Tool Registry
- **`system_monitor.py`**: Cross-platform system telemetry. Gathers CPU, RAM, Disk, Network, and Top Processes. Dynamically falls back from `psutil` to OS-native queries (`powershell`, `df`, `free`, `uptime`).
- **`computer_control.py`**: Python-native mouse automation, keyboard macros, and vision-assisted `screen_find` targeting.
- **`computer_settings.py`**: Native OS hardware manipulation. Utilizes a multi-fallback mechanism (WMI → CIM → nircmd) to aggressively guarantee hardware manipulation.
- **`sandbox.py`**: Securely executes Python, Node.js, Bash, and PowerShell scripts in isolated temporary environments.

### 2.2 Skill Library
The platform ships with **45 Built-In Professional Skills**, including:
- **Core Operations**: Git commits, thorough code reviews, native file editing.
- **Pro Actions**: DevOps templates (Docker Compose, CI/CD, Terraform), Security Scans, OSINT recon, Data Analysis (CSV/JSON).

### 2.3 External Installer (`skills/installer.py`)
JARVIS natively integrates with external massive open-source Skill hubs:
- Users can run `/install-skills claude-skills` or `/install-skills openclaw-master`.
- The installer automatically clones external Git repositories and parses their structures into the native JARVIS YAML/Markdown schema.

---

## 3. Sub-Agent Delegation (`multi_agent/`)

JARVIS can delegate workflows by spinning up **8 isolated sub-agents**, each mimicking specialized personas:
- **`coder`**, **`reviewer`**, **`researcher`**, **`tester`**, **`editor`**, **`general-purpose`**
- **`sysadmin`**: Senior administrator enumerating system configurations and diagnosing service issues.
- **`devops`**: Automating infrastructure schemas, CI/CD pipelines, and server provisioning.

Example: `"JARVIS, spawn a devops agent to build a Dockerfile"` creates a closed loop where the agent executes terminal commands, writes files, and returns to the main orchestrator when complete.

---

## 4. Persistent Memory (`memory/`)
JARVIS does not suffer from context-amnesia between application restarts.
- **ChromaDB Vector Store (`persistent_store.py`)**: All memory blocks are actively synced to local ChromaDB SQLite vector embeddings. High-speed cosine similarity search guarantees that semantic concepts are instantly recalled. Falls back gracefully to precise keyword-matching if the vector database is missing.
- **`consolidator.py`**: Upon exiting (`/quit`), JARVIS synthesizes the short-term working memory into semantic metadata blocks and commits them to `.jarvis/memory/`.

---

## 5. Security & Scope Enforcement (Red Team)

JARVIS MK37 is built for DevSecOps users and ensures strict control over system automation.
- **Permission Modes (`permissions.py`)**: Global enforcement of `ALLOW_ALL`, `CONFIRM_ALL`, and `DENY_ALL`. Mode is controlled by `JARVIS_PERMISSION_MODE` (with fallback to `current_scope.json`), and explicit deny/allow lists are sourced from scope permissions.
- **Persistent Audit Logging**: Every tool execution, payload, and authorization decision is securely logged to `~/.jarvis/audit.log` for forensic rollback.
- **Scope Definitions (`current_scope.json`)**: An explicit JSON schema dictating allowed/excluded IPv4 blocks, target domains, temporal engagement hours, and acceptable actions. Tools explicitly cross-reference the ScopeEnforcer prior to execution.

---

## 6. Deployment & Auto-Startup

- **Cross-Platform Python Architecture**: Critical paths leverage `sys.platform`, absolute pathlib resolution, and `utf-8` encoding enforcements to guarantee operations from WSL instances, Ubuntu Server, macOS, or Windows 11 natively.
- **Windows Auto-Start**: Running `python install_startup.py` injects a silent, invisible VBScript instance into the Windows `Startup` folder. Upon desktop login, it executes the AI voice assistant completely in the background without UI flashes, ensuring the assistant is continually waiting for wake words or hotkeys.
