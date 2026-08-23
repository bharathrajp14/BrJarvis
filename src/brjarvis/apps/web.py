# src/brjarvis/apps/web.py — Canonical Web Server Entry Point for BR JARVIS MK40.2+
from __future__ import annotations

import os
import sys

import uvicorn


def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    import socket

    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port


def main() -> int:
    requested_port = int(os.environ.get("PORT", os.environ.get("BR_SERVER_PORT", "8000")))
    port = find_available_port(requested_port)
    host = os.environ.get("HOST", "127.0.0.1")
    from brjarvis.web.api.server import create_app

    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
