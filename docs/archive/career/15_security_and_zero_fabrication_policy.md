# 15. Security and Zero-Fabrication Policy Specification

## Zero-Fabrication Mandate

1. **Truthfulness Invariant**: Resumes, cover letters, and application materials must accurately reflect verified facts from the canonical `CareerProfile`.
2. **Missing Information Policy**: If a job requirement or question asks for skills, dates, or certifications not present in the profile, BR JARVIS will prompt the candidate or state that it is unverified rather than inventing data.
3. **Fail-Closed Security Engine**: Destructive actions (application submissions, external OAuth tokens) are guarded by policy enforcement gates requiring explicit human confirmation.
