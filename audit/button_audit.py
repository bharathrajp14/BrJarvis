from __future__ import annotations

import re
from pathlib import Path

source = Path('frontend/src/app/App.tsx').read_text(encoding='utf-8')
lines = source.splitlines()
rows = []
for line_number, line in enumerate(lines, start=1):
    if '<button' not in line:
        continue
    for match in re.finditer(r'<button\b(?P<attrs>.*?)(?:</button>|>)', line):
        attrs = match.group('attrs')
        before_close = line[match.start():]
        label = re.sub(r'<[^>]+>', ' ', before_close.split('</button>', 1)[0])
        label = re.sub(r'\{[^}]*\}', ' ', label)
        label = ' '.join(label.split())[:80] or 'icon/button'
        has_click = 'onClick=' in attrs or 'onClick=' in before_close.split('</button>', 1)[0]
        permanent_disabled = 'disabled' in attrs and 'disabled={' not in attrs
        rows.append({
            'line': line_number,
            'label': label,
            'has_onClick': has_click,
            'permanent_disabled': permanent_disabled,
            'aria_label': re.search(r'aria-label="([^"]+)"', attrs).group(1) if re.search(r'aria-label="([^"]+)"', attrs) else '',
        })

report = ['# BRJARVIS Button Audit', '', '| Line | Label / aria-label | Handler | Permanent disabled |', '|---:|---|---|---|']
for row in rows:
    identity = row['aria_label'] or row['label']
    report.append(f"| {row['line']} | {identity.replace('|', '/') } | {'PASS' if row['has_onClick'] else 'MISSING'} | {'YES' if row['permanent_disabled'] else 'NO'} |")
report.extend(['', f'**Total button elements found:** {len(rows)}', f'**Missing handlers:** {sum(not row["has_onClick"] for row in rows)}', f'**Permanent disabled buttons:** {sum(row["permanent_disabled"] for row in rows)}', '', 'A button with no handler or a permanent disabled state is a review item. Navigation and form-submit buttons are considered functional when their parent handler is explicit.'])
Path('audit/BUTTON_AUDIT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
print('\n'.join(report))
