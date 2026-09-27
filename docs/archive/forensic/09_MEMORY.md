# 09 — MEMORY & KNOWLEDGE GRAPH FORENSIC RECORD

## 1. Overview & Multi-Tier Architecture
BR JARVIS implements a multi-tier memory hierarchy consisting of:
1. **Working Memory** (`memory/working.py`): In-memory sliding window of current session dialogue turns.
2. **Episodic / Conversation Store** (`memory/conversation_store.py`, `history/session_store.py`): SQLite database storing full session transcripts with timestamp indexing.
3. **Semantic Vector Store** (`memory/vector_store.py`): ChromaDB & SQLite vector store with Gemini embedding embeddings.
4. **Knowledge Graph** (`memory/knowledge_graph.py`, `memory/temporal_kg.py`): Entity-relationship graph with temporal validity edges (`valid_from`, `valid_to`).
5. **Procedural Lessons** (`memory/lessons.py`): Self-correcting feedback store logging previous errors and user corrections.
6. **Encrypted Contact Store** (`memory/contact_manager.py`, 728 lines): AES-GCM encrypted CRM database for personal phone numbers, emails, and relationships.

---

## 2. Memory Subsystem File-by-File Analysis

### `memory/unified_memory.py` (206 lines)
- **Role**: Unified memory coordinator facade (`UnifiedMemoryManager`).
- **Methods**: `query_memory(query, top_k)`, `store_interaction(role, content)`, `consolidate_session()`.
- **Hybrid Retrieval**: Combines semantic cosine similarity search + BM25 keyword matching + temporal recency decay scoring.
- **Disposition**: **KEEP + IMPROVE**.

### `memory/vector_store.py` (320 lines)
- **Role**: Vector database adapter.
- **Backends**: Supports `chromadb` persistent client and a lightweight pure-Python SQLite vector store using NumPy dot products.
- **Embedding Model**: `text-embedding-004` (Gemini) with local TF-IDF fallback.
- **Disposition**: **KEEP**.

### `memory/contact_manager.py` (728 lines)
- **Role**: Personal contacts and relationship manager.
- **Security**: Uses Fernet / AES symmetric encryption (`contacts.key`) to store sensitive personal data in `.jarvis/contacts.json`.
- **Disposition**: **KEEP + IMPROVE**.

### `memory/decay.py` (67 lines)
- **Role**: Ebbinghaus exponential forgetting curve implementation (`calculate_retention(initial_strength, elapsed_days)`).
- **Disposition**: **KEEP**.

---

## 3. Discovered Storage Fragmentation
The memory subsystem currently writes to **8 separate physical stores**:
1. `memory_db/chroma.sqlite3` (ChromaDB vectors)
2. `memory_db/lessons.db` (Lessons & reflections)
3. `memory_db/tf_idf_memory.json` (TF-IDF keyword cache)
4. `.jarvis/app_tracker.db` (Application usage statistics)
5. `.jarvis/calendar.db` (Calendar events)
6. `.jarvis/contacts.json` (Encrypted contacts)
7. `.jarvis/memory/` (Markdown session notes)
8. `memory/processed_messages.db` (Message deduplication cache)

*Remediation*: Consolidate all relational tables into a single unified SQLite database (`.jarvis/jarvis_core.db`) with distinct tables and single-writer concurrency locks (`memory/sqlite_lock.py`).
