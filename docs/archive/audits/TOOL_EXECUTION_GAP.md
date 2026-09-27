# TOOL EXECUTION GAP AUDIT REPORT

**Audit Objective:** Identify tools that are registered but return fake/mock data, fail during execution, or lack end-to-end runtime paths.

## 1. Mock Stubs & False Success in `tools/app_connectors.py`

### Problem Found
`tools/app_connectors.py` contained hardcoded mock JSON dictionaries returning fake success for:
- `gmail_list_unread` (returned 3 hardcoded fake emails)
- `gmail_send_email` (returned `status: success` without sending email)
- `notion_search_pages` (returned hardcoded fake Notion URLs)
- `notion_create_page` (returned fake success message)
- `github_list_prs` (returned hardcoded fake PRs #36 and #37)
- `github_create_issue` (returned hardcoded fake issue #42)
- `calendar_list_events` (returned hardcoded fake events)

### Remediation Applied
Rewired `tools/app_connectors.py` to route directly through `connectors.hub.get_hub()` and the real connector classes (`GitHubConnector`, `GmailConnector`, `NotionConnector`, `SlackConnector`, `CalendarConnector`).
If a service is unconfigured (e.g. `GITHUB_TOKEN` is missing), the tool now returns `BLOCKED_BY_CREDENTIAL` with exact setup instructions rather than fabricating success.

## 2. Tool Argument Schema vs Handler Signature Alignments

All registered tools now accept flexible parameter invocation: both direct positional/keyword arguments and single dictionary payloads (`args: dict`), preventing `TypeError: unexpected keyword argument` runtime crashes during LLM function calling.

## 3. Sandboxed Code Execution Execution Path

`run_code` and `scratchpad_eval` execute securely inside `tools/sandbox_process.py` with process isolation, strict timeout enforcement, and stdout/stderr capture.