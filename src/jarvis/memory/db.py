"""Canonical SQLite connection manager in WAL mode with serialized write locks.

Invariant: Only memory/db.py opens a SQLite connection; every write goes through
the connection serializer lock.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_WRITE_LOCK = threading.RLock()


class Database:
    """Manages SQLite connections with WAL mode and thread-safe write locks."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._ensure_parent_dir()

    def _ensure_parent_dir(self) -> None:
        if self.db_path != Path(":memory:"):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """Create a configured SQLite connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None,  # autocommit mode; transactions managed explicitly
        )
        conn.row_factory = sqlite3.Row
        # Enable WAL mode and performance pragmas
        if self.db_path != Path(":memory:"):
            conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=30000;")
        return conn

    @contextmanager
    def read_connection(self) -> Iterator[sqlite3.Connection]:
        """Provide a connection for concurrent read operations."""
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def write_transaction(self) -> Iterator[sqlite3.Connection]:
        """Provide an exclusive, serialized connection for write transactions."""
        with _WRITE_LOCK:
            conn = self.connect()
            try:
                conn.execute("BEGIN IMMEDIATE;")
                yield conn
                if conn.in_transaction:
                    conn.execute("COMMIT;")
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK;")
                raise
            finally:
                conn.close()
