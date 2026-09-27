# 09. Manual Application Assistant & Platform Policy Specification

## Platform Policy Governance

| Platform | Policy State | Automation Mode | Sensitive Guard |
| :--- | :--- | :--- | :--- |
| **Greenhouse** | `REVIEW_REQUIRED` | API Discovery + Assisted Browser Form Handoff | Human Confirmation Mandated |
| **Lever** | `REVIEW_REQUIRED` | API Discovery + Assisted Browser Form Handoff | Human Confirmation Mandated |
| **Ashby** | `REVIEW_REQUIRED` | API Discovery + Assisted Browser Form Handoff | Human Confirmation Mandated |
| **LinkedIn** | `MANUAL_REQUIRED` | Manual User Handoff (Anti-Bot Safeguard) | Full Manual Control |
| **Indeed** | `MANUAL_REQUIRED` | Manual User Handoff | Full Manual Control |
| **Unknown** | `MANUAL_REQUIRED` | Fail-Closed Manual Review | Full Manual Control |

## Sensitive Field Guard
Under NO circumstances will BR JARVIS automatically guess or submit answers to:
- Work authorization status
- Visa sponsorship requirements
- Target or historical compensation
- Equal Employment Opportunity (EEO) demographic disclosures
- Criminal background disclosures
