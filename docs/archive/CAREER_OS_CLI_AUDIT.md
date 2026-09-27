# BR JARVIS MK40.2+ — Career OS CLI Interface Audit

## CLI Command Suite (`core/terminal/commands.py`)

| Command | Subcommands / Flags | Description |
| :--- | :--- | :--- |
| `/career` | `stats`, `sync`, `onboard`, `analytics` | Complete profile review, completeness, pipeline telemetry, and Excel sync |
| `/applications` | `followup` | List active CRM applications and check overdue/pending follow-up milestones |
| `/interviews` | — | Display upcoming interview rounds, dates, times, timezones, and meeting URLs |
| `/offers` | — | List detected job offers, compensation, conditions, and expiry dates |
| `/emails` | — | View parsed recruitment email activity feed with 16-category classifications |
| `/resume` | `[role]`, `tailor` | Generate, tailor, and export resumes across HTML, DOCX, and PDF formats |
| `/jobs` | `<query>` | Search and match live postings across Greenhouse, Lever, and Ashby portals |
| `/apply` | `<job_id>` | Prepare application package and open portal in browser with manual assistance |
| `/ats` | `[role]` | Run 7-factor deterministic ATS compatibility audit against target role |
