# 01. BR JARVIS Career OS — Master Architecture Specification

## Overview

**BR JARVIS MK40.2 Career OS** is a production-grade, authoritative Career Operating System natively integrated into BR JARVIS. It transforms fragmented job seeking into an automated, verified, high-throughput career intelligence and execution lifecycle.

```
+-------------------------------------------------------------------------+
|                        Unified Career Profile                           |
|      (Single Source of Truth, Provenance-Tracked, Zero-Fabrication)     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                        Career Intelligence Engine                       |
|           (Onboarding Interview, Gap Analysis, Career Memory)           |
+-------------------------------------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|     Resume Engine     |                       |      Job Engine       |
|  10 Native Templates  |                       |  Greenhouse, Lever,   |
| ATS Scoring (7-Factor)|                       |    Ashby, Browser     |
|   Tailoring & Diff    |                       | 10-Factor Job Matcher |
+-----------------------+                       +-----------------------+
            |                                               |
            +-----------------------+-----------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                           Application Engine                            |
|       (Platform Policy Gate, Sensitive Field Guard, Package Builder)    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                      Universal Execution Runtime                        |
|       (Headless Browser Sandbox, Verification Gates, Evidence Audit)    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                   Application Tracker & Funnel Analytics                |
|      (15-Status State Machine, Telemetry, Interview Prep Kit)           |
+-------------------------------------------------------------------------+
```

## Architectural Invariants

1. **Profile is Canonical**: Resumes are views. Tailoring selects and emphasizes verified facts; it never mutates the underlying profile.
2. **Zero Fabrication**: No hallucinations of experience, skills, dates, metrics, degrees, or certifications. Missing fields trigger interactive user questions.
3. **Fail-Closed Verification**: No application is reported as submitted without physical evidence (Confirmation ID, receipt URL, or verified HTTP API response).
4. **Policy-Bound Automation**: Anti-bot protections, CAPTCHAs, and sensitive legal fields mandate human review.
