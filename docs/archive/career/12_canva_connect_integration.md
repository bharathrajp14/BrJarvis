# 12. Canva Connect API Integration Specification

## Architecture & Fallback

- **Authentication**: Secure OAuth tokens stored in isolated config (`config/canva_credentials.json`).
- **Autofill Dataset**: Maps `ResumeSchema` attributes directly to Canva Connect Autofill schema.
- **Dynamic Capability Probing**: Inspects API connectivity on demand.
- **Authoritative Native Fallback**: If Canva Connect API credentials are not configured, BR JARVIS seamlessly routes to the Native Premium Resume Engine without false claims or broken workflows.
