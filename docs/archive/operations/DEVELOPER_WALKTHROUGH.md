# JARVIS MK38 — Developer Walkthrough

A complete guide to setting up, configuring, and developing with the JARVIS MK38 AI assistant platform.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running JARVIS](#running-jarvis)
6. [Architecture Overview](#architecture-overview)
7. [Working with Tools](#working-with-tools)
8. [Working with Skills](#working-with-skills)
9. [Sub-Agent Delegation](#sub-agent-delegation)
10. [Memory & Persistence](#memory--persistence)
11. [Security & Permissions](#security--permissions)
12. [Development Workflow](#development-workflow)
13. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **OS**: Windows 10+, macOS (Intel/Apple Silicon), or Linux (Ubuntu 20.04+)
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 2GB free space
- **Internet**: Required for API backends (optional if using Ollama locally)

### Required Accounts

- **Google Gemini API** — Get at: https://aistudio.google.com/app/apikey (**REQUIRED**)
- Optional accounts for enhanced functionality:
  - Anthropic (Claude)
  - OpenAI (GPT)
  - Mistral AI
  - NVIDIA NIM (for GPU acceleration)

### System Tools (OS-Specific)

**Windows:**
- PowerShell 5.0+ (usually pre-installed)
- Optional: `nircmd` for advanced hardware control

**macOS/Linux:**
- `ffmpeg` for audio processing
- `xclip` or `xsel` (Linux only, for clipboard)
- `sox` (optional, for enhanced audio)

---

## Environment Setup

### Step 1: Clone the Repository

```bash
cd g:\MARKJARVIS
git clone https://github.com/bharthraj1412/Jarvis-MK37.git
cd Jarvis-MK37
```

### Step 2: Create a Python Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux (Bash/Zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Verify Python Version

```bash
python --version
# Expected output: Python 3.11.x or higher
```

### Step 4: Upgrade pip

```bash
python -m pip install --upgrade pip
```

---

## Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements_mk37.txt
```

**What gets installed:**
- LLM Backends: `anthropic`, `openai`, `google-genai`, `mistralai`
- Vector DB: `chromadb`, `sentence-transformers`
- Tools: `playwright`, `pyautogui`, `requests`, `duckduckgo-search`
- Web: `fastapi`, `uvicorn`, `websockets`
- UI: `rich`
- Audio: `sounddevice`, `python-dotenv`

### Step 2: Verify Installation (Optional but Recommended)

Run the smoke test to ensure all dependencies are properly installed:

```bash
python scripts/smoke_startup.py
```

This performs non-destructive preflight checks on:
- Python environment
- Required packages
- Backend availability
- Tool registry
- Configuration files

---

## Configuration

### Step 1: Create Environment File

Copy the template to `.env`:

```bash
cp .env.template .env
```

### Step 2: Add Your Gemini API Key (REQUIRED)

Edit `.env` and replace with your actual key:

```bash
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

Get your key at: https://aistudio.google.com/app/apikey

### Step 3: Add Optional Backend Keys

Uncomment and fill in keys for additional backends you have:

```bash
# Uncomment these and add your keys if available:
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
MISTRAL_API_KEY=your_mistral_key
NVIDIA_API_KEY=your_nvidia_key
OLLAMA_HOST=http://localhost:11434
```

### Step 4: Configure Models (Optional)

Override default model selections:

```bash
JARVIS_MODEL_GEMINI=gemini-2.5-flash
JARVIS_MODEL_CLAUDE=claude-sonnet-4-20250514
JARVIS_DEFAULT_BACKEND=gemini
```

### Step 5: Set Permission Mode (Optional)

Control tool execution restrictions:

```bash
# Options: allow_all (default) | confirm_destructive | confirm_all
JARVIS_PERMISSION_MODE=allow_all
```

### Step 6: Deny Tools (Optional)

Restrict specific tools:

```bash
# Comma-separated list of tool names to block
JARVIS_DENY_TOOLS=restart,shutdown
```

### Step 7: Verify Configuration

Check that your configuration loads correctly:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('GEMINI_API_KEY:', 'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET')"
```

---

## Running JARVIS

### Option 1: Voice Interface (Recommended for First Run)

The voice interface is interactive and great for exploration:

```bash
python main.py
```

**Features:**
- Real-time voice conversation
- Wake word detection
- Screen vision integration
- Natural spoken responses via text-to-speech
- Accessible UI with response history

**Usage:**
- Speak to activate
- Say "stop" or "quit" to exit
- Naturally describe tasks

### Option 2: CLI Orchestrator (Professional, DevOps-Focused)

The CLI is powerful for automation and chaining tasks:

```bash
python main_mk37.py
```

**Features:**
- Rich terminal UI with syntax highlighting
- Explicit slash commands
- Multi-step task chaining
- Full memory and audit logging
- Ideal for scripting and automation

**Common Commands:**
```bash
# Task execution
/task "describe your task here"

# View available tools
/tools

# List available skills
/skills

# Install external skills
/install-skills claude-skills

# View memory
/memory

# Check system status
/status

# Change permission mode
/permission allow_all

# Exit gracefully
/quit
```

### Option 3: Quick Command Execution (Headless)

Execute a single command without interactive mode:

```bash
python -c "from router import AgentRouter; r = AgentRouter({}); print(r.quick('Explain quantum computing'))"
```

---

## Architecture Overview

### Core Components

```
Jarvis-MK37/
├── router.py              # Multi-backend LLM routing engine
├── orchestrator.py        # Main task orchestration
├── permissions.py         # Security & scope enforcement
├── main.py               # Voice interface
├── main_mk37.py          # CLI orchestrator
│
├── config/               # Configuration management
│   ├── models.json       # Model definitions
│   ├── api_keys.json     # API key management
│   └── model_loader.py   # Dynamic model loading
│
├── agent/                # Core agent logic
│   ├── executor.py       # Tool execution engine
│   ├── planner.py        # Task planning & decomposition
│   ├── task_queue.py     # Async task management
│   └── error_handler.py  # Graceful error handling
│
├── actions/              # Tool implementations (47 tools)
│   ├── web_search.py     # Web & search tools
│   ├── computer_control.py # Desktop automation
│   ├── system_monitor.py # System telemetry
│   ├── code_helper.py    # Code analysis & generation
│   └── ... (43 more tools)
│
├── memory/               # Persistent memory system
│   ├── memory_manager.py # Memory lifecycle
│   ├── persistent_store.py # ChromaDB integration
│   ├── consolidator.py   # Memory consolidation
│   └── vector_store.py   # Semantic search
│
├── multi_agent/          # Sub-agent delegation
│   └── subagent.py       # Isolated worker spawning
│
├── skills/               # Reusable skill templates
│   ├── builtin.py        # Core skills
│   ├── executor.py       # Skill execution
│   ├── loader.py         # Dynamic loading
│   └── ... (45+ skills)
│
├── redteam/              # Security & auditing
│   ├── scope.py          # Scope definitions
│   ├── recon.py          # OSINT reconnaissance
│   ├── report.py         # Security reporting
│   └── vuln_scanner.py   # Vulnerability scanning
│
├── history/              # Session & audit trails
│   ├── session_store.py  # Session persistence
│   ├── audit_writer.py   # Forensic logging
│   └── replay.py         # Session replay
│
├── tools/                # MCP & tool integration
│   ├── registry.py       # Tool registry
│   ├── sandbox.py        # Safe execution sandbox
│   ├── mcp_connector.py  # Model Context Protocol
│   └── web.py            # Web integrations
│
└── screen_server/        # Screen sharing
    ├── ws_server.py      # WebSocket server
    └── viewer.html       # Web viewer
```

### Request Flow

```
User Input (Voice/CLI)
    ↓
Router (Multi-Backend Selection)
    ↓
Planner (Task Decomposition)
    ↓
Orchestrator (Coordination)
    ↓
Executor (Tool Invocation)
    ├─ Tool 1 (Deterministic)
    ├─ Tool 2 (API Call)
    └─ Tool N (Sandboxed Code)
    ↓
Memory Manager (Persistence)
    ↓
Response Generation
    ↓
Output (Voice/CLI/Display)
```

---

## Working with Tools

### Understanding Tools

JARVIS includes 47 deterministic tools categorized as:

- **System Tools**: CPU/RAM monitoring, process management
- **Control Tools**: Mouse, keyboard, screen capture
- **Web Tools**: Search, browser automation, web scraping
- **File Tools**: Read, write, directory operations
- **Code Tools**: Execution sandboxes, linting, analysis
- **Integration Tools**: APIs, webhooks, external services
- **Security Tools**: Scanning, reconnaissance, auditing

### Viewing Available Tools

**In CLI Orchestrator:**
```bash
/tools
```

**Programmatically:**
```python
from tools.registry import ToolRegistry

registry = ToolRegistry()
for tool in registry.list_tools():
    print(f"{tool.name}: {tool.description}")
```

### Using Tools in Code

**Example: Web Search**

```python
from actions.web_search import WebSearch

searcher = WebSearch()
results = searcher.search("latest AI news", max_results=5)
for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Summary: {result['snippet']}\n")
```

**Example: System Monitor**

```python
from actions.system_monitor import SystemMonitor

monitor = SystemMonitor()
stats = monitor.get_stats()
print(f"CPU Usage: {stats['cpu']}%")
print(f"Memory Usage: {stats['memory']}%")
print(f"Top Processes: {stats['top_processes']}")
```

**Example: Code Sandboxing**

```python
from tools.sandbox import Sandbox

sandbox = Sandbox()
result = sandbox.execute_python("""
import math
print(f"Pi rounded to 2 decimals: {round(math.pi, 2)}")
""")
print(result.stdout)
```

### Adding New Tools

Create a new file in `actions/` following this template:

```python
# actions/my_new_tool.py

class MyNewTool:
    """
    Description of what this tool does.
    
    Returns:
        dict: Result structure with 'success' and 'data' keys
    """
    
    def __init__(self):
        self.name = "my_new_tool"
        self.description = "Clear description for LLM routing"
    
    def execute(self, **kwargs):
        """Execute the tool with given parameters."""
        try:
            # Implementation
            result = self._do_work(**kwargs)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _do_work(self, **kwargs):
        # Your tool logic here
        pass
```

Register it in `tools/registry.py`:

```python
from actions.my_new_tool import MyNewTool

# Add to tool registry
registry.register(MyNewTool())
```

---

## Working with Skills

### Understanding Skills

Skills are reusable prompt templates that combine:
- **System instructions**: Context and persona
- **User template**: Dynamic placeholders for input
- **Tools**: Associated tool calls
- **Format**: YAML metadata + Markdown content

### Built-In Skills

Available via `/skills` command. Common skills:

- **code_review**: Thorough code analysis
- **security_audit**: DevSecOps assessment
- **docker_compose**: Infrastructure templates
- **data_analysis**: CSV/JSON processing
- **git_workflow**: Version control guidance

### Creating Custom Skills

Create a new file in `skills/`:

```yaml
# skills/my_skill.yaml

name: "my_skill"
description: "What this skill does"
category: "custom"
author: "Your Name"
version: "1.0.0"

tools:
  - web_search
  - code_helper

parameters:
  - name: topic
    description: "Main topic to analyze"
    required: true
  - name: depth
    description: "Analysis depth (basic/detailed)"
    default: "detailed"
```

The Markdown content follows:

```markdown
# My Skill

## Instructions for the LLM

You are an expert in {{topic}}. Provide a {{depth}} analysis covering:

1. Key concepts
2. Practical applications
3. Best practices
4. Common pitfalls

Use the web_search tool to find current information.
```

### Using Skills in Code

```python
from skills.loader import SkillLoader

loader = SkillLoader()
skill = loader.load("my_skill")
result = skill.execute(topic="Machine Learning", depth="detailed")
print(result)
```

### Installing External Skills

From the CLI:

```bash
/install-skills claude-skills
/install-skills openclaw-master
```

This clones external repositories and auto-parses their skill structures.

---

## Sub-Agent Delegation

### Understanding Sub-Agents

Spawn specialized workers to parallelize tasks:

- **coder**: Code generation and debugging
- **reviewer**: Code review and auditing
- **researcher**: Research and data gathering
- **tester**: Test generation and validation
- **editor**: Content writing and editing
- **sysadmin**: System configuration and diagnostics
- **devops**: Infrastructure and deployment
- **general-purpose**: Flexible multi-domain tasks

### Using Sub-Agents from CLI

```bash
# Spawn a coder to build a Python web scraper
/agent coder "create a Selenium-based web scraper for e-commerce sites"

# Spawn a devops agent to create a Docker setup
/agent devops "write a Docker Compose for a microservices architecture"

# Spawn multiple agents in parallel
/agent coder "optimize this Python function" &
/agent reviewer "review the security of this API" &
```

### Using Sub-Agents Programmatically

```python
from multi_agent.subagent import SubAgent

# Create a coder sub-agent
coder = SubAgent("coder")
result = coder.execute("Create a FastAPI REST API with OpenAPI docs")
print(result.output)

# Monitor execution
if result.success:
    print("✓ Task completed successfully")
    print(result.files_created)
else:
    print("✗ Task failed:", result.error)
```

### Sub-Agent Architecture

```
Main Orchestrator
    ├─ Sub-Agent 1 (Coder)
    │   ├─ Router
    │   ├─ Planner
    │   └─ Executor
    ├─ Sub-Agent 2 (DevOps)
    │   ├─ Router
    │   ├─ Planner
    │   └─ Executor
    └─ Sub-Agent N (General-Purpose)
        ├─ Router
        ├─ Planner
        └─ Executor
```

Each operates independently with:
- Isolated context windows
- Parallel execution
- Automatic synchronization
- Failure isolation

---

## Memory & Persistence

### Memory System Overview

JARVIS never forgets. The memory system includes:

1. **Working Memory**: Current session context (RAM)
2. **Vector Store**: ChromaDB semantic embeddings (SQLite backend)
3. **Session Store**: Complete conversation history
4. **Audit Log**: Every action and decision

### Accessing Memory from CLI

```bash
# View memory statistics
/memory stats

# Search memory by keyword
/memory search "Python decorators"

# Search semantically
/memory semantic "how do I handle async tasks?"

# View session history
/memory history

# Export memory snapshot
/memory export myexport.json
```

### Memory Consolidation

When exiting JARVIS (`/quit`), the system:

1. Synthesizes short-term context into semantic blocks
2. Computes embeddings for vector search
3. Commits to persistent storage (`~/.jarvis/memory/`)
4. Preserves for next session

### Working with Memory Programmatically

```python
from memory.memory_manager import MemoryManager
from memory.vector_store import VectorStore

# Initialize
memory = MemoryManager()
vector_store = VectorStore()

# Add to memory
memory.add("Important concept X", "my-context")

# Semantic search
results = vector_store.search("how to optimize performance", top_k=5)
for result in results:
    print(f"Score: {result.score}, Text: {result.text}")

# Get full memory context
context = memory.get_context_for_task("build microservice")
print(context)
```

### Memory Data Location

```
~/.jarvis/
├── memory/
│   ├── consolidated_blocks.json     # Semantic memory blocks
│   ├── session_metadata.json         # Session metadata
│   └── relationships.json            # Concept linkage
├── memory_db/
│   └── chroma.sqlite3                # Vector embeddings
└── audit.log                          # Complete audit trail
```

---

## Security & Permissions

### Permission Modes

Control what tools can execute without confirmation:

**1. allow_all (Default)**
- Tools execute immediately
- Best for development and testing
- Set with: `JARVIS_PERMISSION_MODE=allow_all`

**2. confirm_destructive**
- Requires confirmation for risky operations
- Safe operations execute immediately
- Risky: file deletion, system restart, etc.
- Set with: `JARVIS_PERMISSION_MODE=confirm_destructive`

**3. confirm_all**
- Every tool execution requires approval
- Most secure but slowest
- Ideal for production with sensitive systems
- Set with: `JARVIS_PERMISSION_MODE=confirm_all`

### Scope Definitions

Define allowed targets and operations in `current_scope.json`:

```json
{
  "permission_mode": "confirm_destructive",
  "allowed_ips": ["192.168.1.0/24", "10.0.0.0/8"],
  "denied_ips": ["192.168.1.100"],
  "allowed_domains": ["github.com", "api.openai.com"],
  "denied_domains": ["malicious.com"],
  "max_execution_time_seconds": 300,
  "deny_tools": ["restart", "format_disk"],
  "audit_log_path": "~/.jarvis/audit.log"
}
```

### Audit Logging

Every action is logged with:
- Timestamp
- Tool name and parameters
- Result (success/failure)
- Authorization decision
- User or agent identifier

View audit log:

```bash
# Windows
Get-Content ~/.jarvis/audit.log -Tail 50

# Linux/macOS
tail -50 ~/.jarvis/audit.log
```

### Implementing Scope Enforcement

```python
from redteam.scope import ScopeEnforcer

enforcer = ScopeEnforcer.from_file("current_scope.json")

# Check permission before executing
if enforcer.is_allowed_tool("restart"):
    perform_restart()
else:
    print("Tool 'restart' is denied in current scope")

# Check IP scope
if enforcer.is_allowed_ip("192.168.1.50"):
    connect_to_device()
```

---

## Development Workflow

### Setting Up Your Development Environment

1. **Clone & Setup**
   ```bash
   git clone <repo>
   cd Jarvis-MK37
   python -m venv .venv
   source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements_mk37.txt
   ```

2. **Pre-Commit Checks**
   ```bash
   python scripts/smoke_startup.py
   ```

3. **Run Tests**
   ```bash
   python -m pytest tests/ -v
   ```

### Code Structure & Conventions

**File Organization:**
- Actions in `actions/` (one tool per file)
- Skills in `skills/` (YAML + Markdown)
- Sub-agents in `multi_agent/`
- Tests in `tests/` (mirror source structure)

**Naming Conventions:**
- Tools: `verb_noun.py` (e.g., `web_search.py`)
- Classes: PascalCase (e.g., `WebSearch`)
- Functions: snake_case (e.g., `get_results()`)
- Constants: UPPER_SNAKE_CASE

**Documentation:**
- Module docstrings: Purpose and exports
- Class docstrings: Role and state
- Function docstrings: Parameters, returns, raises

### Adding a New Backend

Create a new file like `<provider>_backend.py`:

```python
# backends/new_backend.py

class NewBackend:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NEW_BACKEND_API_KEY")
        self.name = "new_backend"
        self.model = os.getenv("JARVIS_MODEL_NEW", "default-model")
    
    def chat(self, messages, **kwargs):
        """
        Send messages and get response.
        
        Args:
            messages: List of {"role": "user"/"assistant", "content": "..."}
            **kwargs: Additional parameters
        
        Returns:
            Response text
        """
        # Implementation
        pass
    
    def is_available(self):
        """Check if backend is properly configured."""
        return bool(self.api_key)
```

Register in `router.py`:

```python
from backends.new_backend import NewBackend

# Add to available backends
self.backends['new_backend'] = NewBackend()
```

### Testing Your Changes

**Unit Tests:**
```bash
python -m pytest tests/test_my_tool.py -v
```

**Integration Tests:**
```bash
python test_integration.py
```

**Smoke Test (All Systems):**
```bash
python scripts/smoke_startup.py
```

### Debugging

**Enable Verbose Logging:**
```bash
set JARVIS_LOG_LEVEL=DEBUG
python main_mk37.py
```

**Use the Python Debugger:**
```bash
python -m pdb main.py
```

**Check Configuration:**
```bash
python -c "from router import AgentRouter; r = AgentRouter({}); r.diagnose()"
```

---

## Troubleshooting

### Common Issues & Solutions

#### Issue: "GEMINI_API_KEY not found"

**Solution:**
```bash
# Verify .env exists in project root
ls -la .env  # Linux/macOS
dir .env    # Windows

# Check key is set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('KEY SET' if os.getenv('GEMINI_API_KEY') else 'KEY MISSING')"

# Regenerate from template
cp .env.template .env
# Then edit .env with your actual key
```

#### Issue: "Module not found" errors

**Solution:**
```bash
# Verify virtual environment is activated
which python  # Should show .venv path

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements_mk37.txt --force-reinstall

# Check specific package
python -c "import anthropic; print(anthropic.__version__)"
```

#### Issue: Audio not working

**Solution:**
```bash
# Verify sounddevice is working
python -c "import sounddevice; print(sounddevice.query_devices())"

# Test audio recording
python -c "import sounddevice; import numpy; recording = sounddevice.rec(int(22050 * 3), samplerate=22050); sounddevice.wait(); print('Recorded', len(recording), 'samples')"

# On Windows, may need audio drivers updated
```

#### Issue: Playwright browser fails to load

**Solution:**
```bash
# Install Playwright browsers
playwright install

# Update Playwright
pip install --upgrade playwright

# Clear cache
rm -rf ~/.cache/ms-playwright  # Linux/macOS
rmdir %APPDATA%\.playwright /s /q  # Windows
```

#### Issue: ChromaDB connection errors

**Solution:**
```bash
# Check database integrity
python -c "import chromadb; client = chromadb.Client(); print('Connected')"

# Reset database (destructive)
rm -rf memory_db/  # Linux/macOS
rmdir memory_db /s /q  # Windows

# Restart JARVIS to recreate
```

#### Issue: Tools not appearing in registry

**Solution:**
```bash
# Verify tool is properly registered
python -c "from tools.registry import ToolRegistry; r = ToolRegistry(); print([t.name for t in r.list_tools()])"

# Check imports in __init__.py
cat tools/__init__.py

# Verify tool has proper class structure
grep "def execute" actions/my_tool.py
```

### Debug Commands

**Health Check:**
```bash
python scripts/smoke_startup.py
```

**Detailed Configuration:**
```python
from router import AgentRouter
from config.model_loader import ModelLoader

loader = ModelLoader()
print("Available Models:", loader.list_available_models())
print("Active Backends:", loader.list_active_backends())
```

**Memory Diagnostics:**
```python
from memory.memory_manager import MemoryManager

memory = MemoryManager()
print("Memory Size:", len(memory.get_all_blocks()))
print("Vector DB Status:", memory.vector_store.health_check())
```

**Tool Diagnostics:**
```python
from tools.registry import ToolRegistry

registry = ToolRegistry()
for tool in registry.list_tools():
    try:
        result = tool.health_check()
        print(f"✓ {tool.name}: OK")
    except Exception as e:
        print(f"✗ {tool.name}: {e}")
```

---

## Next Steps

### For First-Time Users

1. ✅ Complete [Environment Setup](#environment-setup)
2. ✅ Complete [Installation](#installation)
3. ✅ Run `python scripts/smoke_startup.py`
4. ✅ Start with voice interface: `python main.py`
5. ✅ Explore `/help` command in CLI

### For Developers

1. ✅ Review [Architecture Overview](#architecture-overview)
2. ✅ Create a new tool following [Working with Tools](#working-with-tools)
3. ✅ Create a skill in [Working with Skills](#working-with-skills)
4. ✅ Run tests: `python -m pytest tests/ -v`
5. ✅ Submit PRs following code conventions

### For Advanced Users

1. ✅ Implement [Custom Permission Modes](#security--permissions)
2. ✅ Build [Sub-Agents](#sub-agent-delegation) for specialized workflows
3. ✅ Integrate with external [APIs and MLCPs](tools/mcp_connector.py)
4. ✅ Explore [Red Team Capabilities](redteam/)
5. ✅ Deploy with [Auto-Startup](install_startup.py)

---

## Getting Help

- 📖 **Full Documentation**: See [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)
- 🐛 **Report Issues**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions
- 📧 **Contact**: [Project Author]

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

**Last Updated**: May 2026  
**Maintained by**: [Bharth Raj](https://github.com/bharthraj1412)
