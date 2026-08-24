from __future__ import annotations

import asyncio
import json
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

from starlette.websockets import WebSocketState

from brjarvis.web.api import server
from brjarvis.web.api.routes import websocket as websocket_routes


_GLOBAL_ACTIVE_SENDS = 0
_GLOBAL_PEAK_SENDS = 0


@dataclass(eq=False)
class FakeWebSocket:
    delay: float = 0.0
    fail: bool = False
    sent: int = 0
    active: int = 0
    peak_active: int = 0

    @property
    def client_state(self):
        return WebSocketState.CONNECTED

    async def send_json(self, data: dict) -> None:
        global _GLOBAL_ACTIVE_SENDS, _GLOBAL_PEAK_SENDS
        self.active += 1
        self.peak_active = max(self.peak_active, self.active)
        _GLOBAL_ACTIVE_SENDS += 1
        _GLOBAL_PEAK_SENDS = max(_GLOBAL_PEAK_SENDS, _GLOBAL_ACTIVE_SENDS)
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            if self.fail:
                raise RuntimeError("simulated slow-client failure")
            self.sent += 1
        finally:
            self.active -= 1
            _GLOBAL_ACTIVE_SENDS -= 1


async def benchmark_broadcast(fn, client_count: int, event_count: int, delay: float, fail_ratio: float = 0.0) -> dict:
    global _GLOBAL_PEAK_SENDS
    _GLOBAL_PEAK_SENDS = 0
    clients = [FakeWebSocket(delay=delay, fail=index < int(client_count * fail_ratio)) for index in range(client_count)]
    # Both modules share the same ACTIVE_WEBSOCKETS set and lock.
    server.ACTIVE_WEBSOCKETS.clear()
    server.ACTIVE_WEBSOCKETS.update(clients)
    websocket_routes.ACTIVE_WEBSOCKETS.clear()
    websocket_routes.ACTIVE_WEBSOCKETS.update(clients)
    start = time.perf_counter()
    for index in range(event_count):
        if fn is server.broadcast_log:
            await fn(f"load-event-{index}")
        else:
            await fn("load.event", {"index": index}, task_id="load-task")
    elapsed = time.perf_counter() - start
    total_sent = sum(client.sent for client in clients)
    return {
        "clients": client_count,
        "events": event_count,
        "delay_ms": delay * 1000,
        "fail_ratio": fail_ratio,
        "elapsed_ms": elapsed * 1000,
        "event_p50_ms": elapsed * 1000 / event_count,
        "event_rate": event_count / elapsed if elapsed else 0,
        "sent": total_sent,
        "expected_successful_sends": int(client_count * (1 - fail_ratio)) * event_count,
        "peak_client_send_overlap": max((client.peak_active for client in clients), default=0),
        "peak_global_send_overlap": _GLOBAL_PEAK_SENDS,
    }


async def main() -> None:
    results = []
    for fn in (server.broadcast_log, websocket_routes.broadcast_ws_event):
        for clients in (1, 10, 50, 100):
            results.append(await benchmark_broadcast(fn, clients, event_count=50, delay=0.0))
            results.append(await benchmark_broadcast(fn, clients, event_count=20, delay=0.010))
        results.append(await benchmark_broadcast(fn, 100, event_count=20, delay=0.050, fail_ratio=0.10))
    server.ACTIVE_WEBSOCKETS.clear()
    websocket_routes.ACTIVE_WEBSOCKETS.clear()
    output = {"websocket_broadcast": results}
    Path("audit/websocket_load_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
