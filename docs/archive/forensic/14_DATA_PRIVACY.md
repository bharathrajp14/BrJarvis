# 14 — DATA PRIVACY & SECRETS AUDIT FORENSIC RECORD

## 1. Executive Privacy Assessment
BR JARVIS manages private credentials, local contact books, email tokens, and session transcripts.

---

## 2. Secrets & Personal Data Audit Table
| File / Resource | Type | Encrypted? | Git-Tracked? | Sensitivity | Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `.env` | Environment Config | NO (Plaintext) | Checked in `.gitignore` | CRITICAL | Verify no committed copies in git history |
| `.env.template` | Config Template | NO (Placeholders)| YES | SAFE | Keep as standard setup template |
| `.jarvis/contacts.json` | Personal Contacts | YES (Fernet AES) | YES | HIGH | Ensure key (`contacts.key`) is ignored |
| `.jarvis/contacts.key` | Symmetric Key | NO (Raw Key) | IGNORED | CRITICAL | Keep in `.gitignore`, generate on first boot |
| `memory_db/chroma.sqlite3`| Vector Database | NO | YES | MEDIUM | Local vector embeddings |
| `workspace/browser_user_data/`| Browser Profile | NO (Binary DB) | YES | HIGH | **REMOVE FROM GIT & ADD TO .gitignore** |
| `logs/transcripts/*.jsonl` | Session Logs | NO (Plaintext) | YES | MEDIUM | Ensure secret masking filter is applied |

---

## 3. Secret Masking Verification (`core/logging.py`)
- Verified that `ColoredConsoleFormatter` and `JSONFormatter` execute regex substitution on all strings matching `AIzaSy[A-Za-z0-9-_]{33}`, `sk-ant-[A-Za-z0-9-_]{40,}`, and `sk-[A-Za-z0-9-_]{48}`, replacing them with `[REDACTED_API_KEY]`.
