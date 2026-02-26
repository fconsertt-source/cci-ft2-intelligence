# tests/integration/test_real_time_rollback.py
from datetime import datetime, timezone
from src.domain.policies.trial_policy import TrialPolicy, TrialStatus

def test_time_rollback_detected():
    # Simulate system time = 2026-02-09 12:00 UTC
    now = datetime(2026, 2, 9, 12, 0, tzinfo=timezone.utc)
    
    # Last valid run was yesterday at 12:00 → no rollback
    policy = TrialPolicy(
        installation_time=datetime(2026, 2, 1, tzinfo=timezone.utc),
        trial_duration_days=30,
        last_valid_run_time=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc)
    )
    
    # Now is AFTER last_valid_run_time → OK
    assert policy.evaluate(now) == TrialStatus.ACTIVE

    # Now = 2026-02-08 10:00 (before last_valid_run_time) → TAMPERED
    past_now = datetime(2026, 2, 8, 10, 0, tzinfo=timezone.utc)
    assert policy.evaluate(past_now) == TrialStatus.TAMPERED