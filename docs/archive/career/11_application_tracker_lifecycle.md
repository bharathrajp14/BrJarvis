# 11. Application Tracker Lifecycle Specification

## 15-Status State Machine

```
[DISCOVERED] ──> [SHORTLISTED] ──> [PREPARING] ──> [READY_FOR_REVIEW]
                                                             │
                                                             v
[FAILED] <──── [MANUAL_ACTION_REQUIRED] <──── [SUBMISSION_REQUESTED]
                                                             │
                                                             v
                                                      [SUBMITTED]
                                                             │
                                                             v
                                                  [SUBMISSION_VERIFIED]
                                                             │
                                                             v
                                                       [SCREENING]
                                                             │
                                                             v
                                                       [INTERVIEW]
                                                             │
                                                             v
                                                       [TECHNICAL]
                                                             │
                                              +--------------+--------------+
                                              │                             │
                                              v                             v
                                          [OFFER]                       [REJECTED]
                                              │
                                              v
                                         [WITHDRAWN]
```
