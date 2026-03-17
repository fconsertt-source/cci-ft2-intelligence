from datetime import datetime, timezone

from src.domain.policies.trial_policy import TrialPolicy, TrialStatus


def test_active_when_within_trial_period():
    now = datetime(2025, 4, 10, 12, 0, tzinfo=timezone.utc)
    policy = TrialPolicy(
        installation_time=datetime(2025, 4, 1, 0, 0, tzinfo=timezone.utc),
        trial_duration_days=14,
        last_valid_run_time=None,
    )
    assert policy.evaluate(now) == TrialStatus.ACTIVE


def test_expired_after_trial_end():
    now = datetime(2025, 4, 16, 0, 0, tzinfo=timezone.utc)  # 15 days after install
    policy = TrialPolicy(
        installation_time=datetime(2025, 4, 1, 0, 0, tzinfo=timezone.utc),
        trial_duration_days=14,
        last_valid_run_time=None,
    )
    assert policy.evaluate(now) == TrialStatus.EXPIRED


def test_tampered_on_time_rollback():
    now = datetime(2025, 4, 5, 10, 0, tzinfo=timezone.utc)
    last_run = datetime(2025, 4, 5, 12, 0, tzinfo=timezone.utc)
    policy = TrialPolicy(
        installation_time=datetime(2025, 4, 1, 0, 0, tzinfo=timezone.utc),
        trial_duration_days=14,
        last_valid_run_time=last_run,
    )
    # Simulate system time rolled back to 10:00 (before last run at 12:00)
    assert policy.evaluate(now) == TrialStatus.TAMPERED


def test_active_with_last_run_before_now():
    now = datetime(2025, 4, 5, 14, 0, tzinfo=timezone.utc)
    last_run = datetime(2025, 4, 5, 12, 0, tzinfo=timezone.utc)
    policy = TrialPolicy(
        installation_time=datetime(2025, 4, 1, 0, 0, tzinfo=timezone.utc),
        trial_duration_days=14,
        last_valid_run_time=last_run,
    )
    assert policy.evaluate(now) == TrialStatus.ACTIVE
