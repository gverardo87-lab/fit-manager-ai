# tests/__init__.py
"""
FitManager AI Studio - Test Suite

Test organization:
- test_pay_rate.py, test_unpay_rate.py, test_soft_delete_integrity.py, test_sync_recurring.py:
    pytest tests with in-memory DB (run with pytest)
- legacy/: Old test scripts for core/ module (broken, need core/ refactor)
    Referenced deleted modules: WorkoutGeneratorV2, ExerciseArchive, DifficultyLevel
- E2E tests: tools/admin_scripts/test_*.py (require running server)
"""
