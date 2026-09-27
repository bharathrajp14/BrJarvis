# 🎨 BR JARVIS — Desktop & Web UI/UX Design Specification

> **Document Status**: Production Architecture Specification  
> **Subsystems**: Maximum Control Center (`ui.py`), Multi-Tasks Dashboard & Floating Voice Overlay (`floating_voice_ui.py`)  
> **Version**: 38.0.0 (MK38 Architecture)  

---

## 1. Executive Summary

BR JARVIS offers a dual-frontend user experience combining a native Tkinter Maximum Control Center (`ui.py`), a Web PWA Glassmorphic Dashboard (`web/`), and a floating audio HUD overlay (`floating_voice_ui.py`).

---

## 2. Key Interface Innovations (v37.30.0)

1. **🚀 Multi-Task & Sub-Agent Frontend Dashboard (`ui.py`)**:
   - Dedicated tab rendering glossy **Task Cards** with dynamic progress bars, output log previews, and real-time status badges (`RUNNING`, `QUEUED`, `COMPLETED`, `FAILED`).
   - Thread-safe updates dispatched from background agent worker threads via `update_agent_task()`.

2. **Voice Prompt Refinement UI Log**:
   - Transparent UI log stream rendering `Spoken Raw` audio transcription vs `Refined Prompt` (stripping vocal fillers `um`, `uh`, `like`).

3. **Floating Audio Orb HUD (`floating_voice_ui.py`)**:
   - Canvas-rendered floating glass orb visualizing mic audio waveform spectrums, listening states, and live Gemini speech responses.

4. **Web Glassmorphic PWA (`web/`)**:
   - Modern HTML5/CSS3/JavaScript interface connecting to `server.py` via WebSockets for real-time streaming chat, tool logs, and system metrics.

---

## 3. UI Color Palette & Design System

- **Background**: Deep Acrylic Glass `#0A0D14` with `0.85` opacity and Gaussian blur.
- **Accent Primary**: Electric Cyan `#00F0FF` for primary actions, active progress bars, and listening aura.
- **Accent Secondary**: Neon Violet `#7000FF` for reasoning traces and subagent task cards.
- **Status Badges**:
  - `RUNNING`: Cyan `#00F0FF` (animated pulse)
  - `QUEUED`: Amber `#FFB000`
  - `COMPLETED`: Emerald `#00E676`
  - `FAILED`: Crimson `#FF1744`
