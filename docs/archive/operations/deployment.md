# BR JARVIS — PRODUCTION DEPLOYMENT & OPERATION GUIDE

## 1. System Requirements
- **Operating System**: Windows 10/11 (64-bit), Linux (Ubuntu 22.04+), or macOS (Sonoma+).
- **Python Version**: Python 3.10 - 3.12 (Recommended: Python 3.12 64-bit).
- **Hardware Acceleration**: NVIDIA GPU with CUDA 12+ (Optional for local Whisper/VLM).

---

## 2. Standard Installation & Startup
```bash
# 1. Clone repository
git clone https://github.com/bharthraj1412/BrJarvis.git
cd BrJarvis

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies in editable mode
pip install -e .

# 4. Configure environment
cp .env.template .env
# Edit .env to add your API keys (GEMINI_API_KEY, ANTHROPIC_API_KEY, etc.)

# 5. Execute Cold Boot Smoke Verification
python scripts/smoke_startup.py

# 6. Launch BR JARVIS Desktop HUD & Voice Engine
python start.py voice
```
