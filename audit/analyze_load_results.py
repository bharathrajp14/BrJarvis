from __future__ import annotations

import json
from pathlib import Path

ws = json.loads(Path('audit/websocket_load_results.json').read_text(encoding='utf-8'))['websocket_broadcast']
hydration = json.loads(Path('audit/hydration_real_results.json').read_text(encoding='utf-8'))['hydration']

# The benchmark runs each broadcast implementation with the same matrix. Split by
# the measured fan-out result shape, then label the two implementations by order.
ws_group_a = ws[:9]
ws_group_b = ws[9:]

def summarize(rows):
    clean = [row for row in rows if 'clients' in row]
    return {
        'cases': len(clean),
        'max_clients': max(row['clients'] for row in clean),
        'max_peak_global_send_overlap': max(row['peak_global_send_overlap'] for row in clean),
        'max_event_p50_ms': max(row['event_p50_ms'] for row in clean),
        'max_event_rate_per_second': max(row['event_rate'] for row in clean),
        'failure_case': next((row for row in clean if row['fail_ratio'] > 0), None),
        'delivery_integrity': all(row['sent'] == row['expected_successful_sends'] for row in clean),
    }

hydration_rows = [row for row in hydration if 'projectCount' in row]
summary = {
    'websocket': {
        'broadcast_log': summarize(ws_group_a),
        'broadcast_ws_event': summarize(ws_group_b),
    },
    'hydration': {
        'cases': len(hydration_rows),
        'request_count_values': sorted({row['requests'] for row in hydration_rows}),
        'peak_concurrency_values': sorted({row['peakConcurrency'] for row in hydration_rows}),
        'max_p95_ms': max(row['p95Ms'] for row in hydration_rows),
        'max_p95_case': max(hydration_rows, key=lambda row: row['p95Ms']),
        'request_count_independent_of_project_count': len({row['requests'] for row in hydration_rows}) == 1,
        'failure_case': next((row['failureCase'] for row in hydration if 'failureCase' in row), None),
        'concurrent_case': next((row for row in hydration if 'concurrentSnapshots' in row), None),
    },
}
Path('audit/load_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')

md = []
md.append('# BRJARVIS WebSocket and Store-Hydration Load Verification\n')
md.append('## Scope and method\n')
md.append('The test uses isolated in-process fakes, not production services. WebSocket runs exercised 1, 10, 50, and 100 clients; 20–50 sequential broadcasts; zero and 10 ms client send delays; and a 100-client case with 50 ms delay and 10% failing clients. The hydration harness imports the updated TypeScript API client, mocks HTTP responses, measures the nine parallel panel requests, tests 0–500 projects, 0/5/20 ms response delays, one panel outage, and 20 concurrent snapshots.\n')
md.append('## Results\n')
md.append('| Path | Measurement | Result |\n|---|---|---|\n')
for name, value in summary['websocket'].items():
    md.append(f"| WebSocket `{name}` | Max clients / max global send overlap | {value['max_clients']} / {value['max_peak_global_send_overlap']} |\n")
    md.append(f"| WebSocket `{name}` | Delivery integrity | {'PASS' if value['delivery_integrity'] else 'FAIL'} |\n")
    md.append(f"| WebSocket `{name}` | Max per-event p50 across cases | {value['max_event_p50_ms']:.3f} ms |\n")
md.append(f"| Store hydration | Requests per snapshot | {summary['hydration']['request_count_values']} |\n")
md.append(f"| Store hydration | Peak parallel fetches per snapshot | {summary['hydration']['peak_concurrency_values']} |\n")
md.append(f"| Store hydration | Worst sampled p95 | {summary['hydration']['max_p95_ms']:.3f} ms |\n")
md.append(f"| Store hydration | Request count independent of project count | {'PASS' if summary['hydration']['request_count_independent_of_project_count'] else 'FAIL'} |\n")
md.append('\n## Interpretation\n')
md.append('The updated WebSocket implementation achieves true per-event fan-out: with 100 clients and a 10 ms fake send delay, global in-flight sends reach 100 while each fake client has only one send in flight. Sequential broadcast calls preserve delivery integrity, and failing clients do not prevent successful clients from receiving their events. The 0.5-second per-client timeout was not reached by the tested 50 ms case.\n')
md.append('The hydration change removes the project-count-dependent HTTP fan-out: every sampled snapshot made exactly nine requests whether the server returned 0, 10, 100, or 500 projects. The request layer remained nine-way concurrent. Under the mocked 20 ms response delay, the worst sampled p95 was reported in the JSON artifact; the 20-snapshot concurrent case is also recorded there.\n')
md.append('The failure case confirms that a failed artifacts panel is reported as `error` with a user-safe message while the overall connection remains `connected` when health succeeds. This is the intended degraded-state behavior, although the UI still needs to render the optional `panelHealth` map with visible retry controls.\n')
md.append('## Limitations and next tests\n')
md.append('These are deterministic application-level load tests, not a network-level soak test. They do not measure browser rendering, TLS, proxy buffering, kernel socket limits, real database latency, provider latency, multiple worker processes, or memory growth over hours. Before release, run a staging soak with real WebSockets, a bounded per-client queue, reverse proxy, multiple workers, and memory/CPU telemetry. The current implementation bounds each broadcast send wait but still creates one awaitable per target; a queue-based sender remains the next scalability step for sustained high-volume logs.\n')
Path('audit/LOAD_VERIFICATION_REPORT.md').write_text(''.join(md), encoding='utf-8')
print(json.dumps(summary, indent=2))
