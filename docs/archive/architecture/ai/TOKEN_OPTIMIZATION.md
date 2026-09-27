# ⚡ Zero-Token Intent Engine & Token Optimization Specification

> **Module**: `core/intent_engine.py` & `memory/cache.py`  
> **Version**: MK37.31.0  
> **Primary Purpose**: 50+ deterministic 0-token instant intent execution engine, fast FNV-1a frame hashing, and prompt payload minimization.

---

## 1. Zero-Token Deterministic Intent Engine (`core/intent_engine.py`)

BR JARVIS intercepts user requests prior to model dispatch using `DeterministicIntentEngine`. If a prompt matches one of **50+ regex/keyword intent patterns**, it is executed instantly with **0 LLM tokens consumed** and **<5ms latency**.

### Supported Zero-Token Intent Categories (50+ Matchers)

1. **System Diagnostics & Telemetry**:
   - RAM Free / Usage / Garbage Collection (`flush ram`, `clean memory`)
   - CPU Load, Frequency, Core Count (`cpu info`, `cpu load`)
   - Disk Space & Partitions (`disk space`, `disk partitions`)
   - Battery & Power Telemetry (`battery status`, `power status`)
   - System Uptime & Hostname (`uptime`, `hostname`)
   - System Timezone & Clock (`time`, `timezone`)
   - Network Ping Latency & IP (`ping`, `ip address`, `network latency`)

2. **Git & Code Workspace Diagnostics**:
   - Active Git Branch (`git branch`, `current branch`)
   - Recent Git Commits (`recent commits`, `git log`)
   - Workspace Health & Statistics (`project stats`, `workspace health`)
   - Python Environment & Packages (`python version`, `installed packages`, `pip list`)
   - Source Code Metrics (`largest python file`, `python functions count`, `python classes count`)

3. **Desktop & Window Management**:
   - Display Resolution (`display resolution`, `screen size`)
   - Active Window Title (`active window`, `current window`)
   - Show Desktop / Lock Screen (`show desktop`, `lock screen`)
   - App Launchers (`open brave`, `open chrome`, `open notepad`, `open settings`)
   - Deep Audit Test Trigger (`run deep audit`, `verify system`)

---

## 2. Fast FNV-1a Hashing & Payload Optimization

- **FNV-1a Frame Hash Caching**: Vision engine screen captures compute 64-bit FNV-1a hashes. If the screen has not changed (`is_static`), LLM vision inference calls are bypassed completely.
- **Payload Truncation**: Tool outputs are truncated beyond 800 lines with an informative snippet header to prevent prompt explosion.
