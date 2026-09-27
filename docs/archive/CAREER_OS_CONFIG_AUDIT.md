# BR JARVIS MK40.2+ — Career OS Configuration Audit

## Environment Variables & Keys

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `JARVIS_CAREER_TRACKER_PATH` | string | `BR_JARVIS_Career_Tracker.xlsx` | Path to projected Excel workbook |
| `JARVIS_CAREER_PROFILE_DIR` | path | `.jarvis/career/` | Canonical profile JSON directory |
| `JARVIS_CAREER_EXCEL_BACKUP_DIR` | path | `.jarvis/backups/` | Versioned backup storage directory |
| `JARVIS_CAREER_EMAIL_SYNC_HOURS` | int | `24` | Default recruitment email lookback window |
| `JARVIS_CAREER_MATCH_THRESHOLD` | float | `0.70` | Confidence gate for automated matching |
| `JARVIS_CAREER_AUTO_CONFIRM_OFFER`| bool | `false` | Strict safety gate: Auto-confirming offers is prohibited |

## Precedence Policy
1. Explicit runtime override arguments
2. Environment variables (`os.environ`)
3. `.env` file
4. `config/*.json` configuration files
5. Hardcoded defaults in `core/config.py` (`CareerConfig`)
