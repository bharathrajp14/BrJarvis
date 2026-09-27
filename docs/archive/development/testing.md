# BR JARVIS — TEST SUITE EXECUTION & TESTING STRATEGY

## 1. Test Suite Commands
```bash
# Run complete test suite (Unit, Integration, Security, E2E)
pytest tests/ -q

# Run fast unit tests
pytest tests/unit/

# Run end-to-end lifecycle tests
pytest tests/e2e/

# Run security & adversarial tests
pytest tests/adversarial/

# Run cold-boot startup smoke checks (12/12)
python scripts/smoke_startup.py
```
