# BR JARVIS MK40.2+ — Voice Assistant Career Integration Audit

## Natural Spoken Query Routing (`voice/assistant.py`)

| Spoken Voice Command | Subsystem Action | Verbal Spoken Output |
| :--- | :--- | :--- |
| *"Check my ATS score"* | `ATSEngine.evaluate_resume()` | "Your master resume has an ATS compatibility score of 88 percent, rated Grade A." |
| *"Find jobs for me"* | `JobFinder.search_and_match()` | "Found 3 top job matches. Best match is Senior AI Architect at Scale AI with a fit score of 92 percent." |
| *"Show my pending applications"*| `CareerCRMDatabase.list_applications()` | "You have 5 tracked applications. Most recent is for AI Engineer at OpenAI, status submission verified." |
| *"Did I receive any interviews?"*| `CareerCRMDatabase.list_interviews()` | "You have 2 scheduled interviews. Next is Technical Round with Stripe on August 25 at 2:30 PM PST." |
| *"Did I receive any offers?"* | `CareerCRMDatabase.list_offers()` | "You have 1 offer recorded from Cursor for Autonomous AI Architect, status offer detected." |
| *"What applications need follow-up?"* | `CareerFollowupEngine.get_pending_followups()` | "You have 1 application requiring follow-up: OpenAI, due on August 22, 2026." |
| *"Sync career tracker"* | `SpreadsheetProjectionEngine.project()`| "Your career tracker Excel workbook has been projected and verified with the latest database records." |
