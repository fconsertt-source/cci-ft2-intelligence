# tests/unit/test_rules_engine_coverage.py
"""اختبارات تغطية للأسطر الناقصة في rules_engine.py"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.domain.services.rules_engine import (ExpiryRule, FreezeRule,
                                              HeatCriticalRule,
                                              TemperatureWarningRule, ThawRule)


def make_center(**kwargs):
    """مساعد لإنشاء mock center."""
    center = MagicMock()
    center.decision_reasons = []
    center.expiry_date = kwargs.get("expiry_date", None)
    center.is_freeze_stable = kwargs.get("is_freeze_stable", False)
    center.freeze_sensitive = kwargs.get("freeze_sensitive", True)
    center.actions = kwargs.get("actions", {})
    center.critical_temp_limit = kwargs.get("critical_temp_limit", 10.0)
    center.ultra_cold_chain_required = kwargs.get("ultra_cold_chain_required", False)
    center.thaw_start_time = kwargs.get("thaw_start_time", None)
    center.thaw_duration_days = kwargs.get("thaw_duration_days", 70)
    center.has_warning = False
    return center


def make_stats(**kwargs):
    return {
        "has_freeze": kwargs.get("has_freeze", False),
        "freeze_duration": kwargs.get("freeze_duration", 0),
        "has_ccm_violation": kwargs.get("has_ccm_violation", False),
        "heat_duration": kwargs.get("heat_duration", 0),
        "max_temp": kwargs.get("max_temp", 5.0),
        "min_temp": kwargs.get("min_temp", 3.0),
        "avg_temp": kwargs.get("avg_temp", 4.0),
        "critical_temp_limit": kwargs.get("critical_temp_limit", 10.0),
    }


class TestExpiryRule:
    def test_no_expiry_date_returns_none(self):
        rule = ExpiryRule()
        center = make_center(expiry_date=None)
        assert rule.evaluate(center, make_stats()) is None

    def test_invalid_date_format_returns_rejected(self):
        rule = ExpiryRule()
        center = make_center(expiry_date="31/12/2020")
        result = rule.evaluate(center, make_stats())
        assert result == "REJECTED_EXPIRED"

    def test_expired_date_returns_rejected(self):
        rule = ExpiryRule()
        past_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        center = make_center(expiry_date=past_date)
        result = rule.evaluate(center, make_stats())
        assert result == "REJECTED_EXPIRED"

    def test_valid_future_date_returns_none(self):
        rule = ExpiryRule()
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        center = make_center(expiry_date=future_date)
        result = rule.evaluate(center, make_stats())
        assert result is None


class TestFreezeRule:
    def test_freeze_sensitive_returns_rejected(self):
        rule = FreezeRule()
        center = make_center(is_freeze_stable=False)
        stats = make_stats(has_freeze=True, freeze_duration=30)
        assert rule.evaluate(center, stats) == "REJECTED_FREEZE"

    def test_freeze_stable_logs_but_continues(self):
        rule = FreezeRule()
        center = make_center(is_freeze_stable=True)
        stats = make_stats(has_freeze=True, freeze_duration=15)
        result = rule.evaluate(center, stats)
        assert result is None
        assert any("مقاوم" in r for r in center.decision_reasons)

    def test_no_freeze_logs_and_continues(self):
        rule = FreezeRule()
        center = make_center()
        stats = make_stats(has_freeze=False)
        result = rule.evaluate(center, stats)
        assert result is None
        assert any("لم يتم رصد تجميد" in r for r in center.decision_reasons)


class TestHeatCriticalRule:
    def test_exceeds_critical_limit_returns_rejected(self):
        rule = HeatCriticalRule()
        center = make_center(critical_temp_limit=10.0)
        stats = make_stats(max_temp=12.0, has_ccm_violation=False)
        assert rule.evaluate(center, stats) == "REJECTED_HEAT_C"

    def test_ccm_violation_returns_rejected(self):
        rule = HeatCriticalRule()
        center = make_center(critical_temp_limit=10.0)
        stats = make_stats(max_temp=5.0, has_ccm_violation=True, heat_duration=700)
        assert rule.evaluate(center, stats) == "REJECTED_HEAT_C"

    def test_within_limits_returns_none(self):
        rule = HeatCriticalRule()
        center = make_center(critical_temp_limit=10.0)
        stats = make_stats(max_temp=5.0, has_ccm_violation=False)
        result = rule.evaluate(center, stats)
        assert result is None


class TestTemperatureWarningRule:
    def test_below_min_sets_warning(self):
        rule = TemperatureWarningRule()
        center = make_center()
        stats = make_stats(min_temp=1.0, max_temp=5.0)
        result = rule.evaluate(center, stats)
        assert result is None
        assert center.has_warning is True

    def test_above_max_sets_warning(self):
        rule = TemperatureWarningRule()
        center = make_center()
        stats = make_stats(min_temp=3.0, max_temp=9.0)
        result = rule.evaluate(center, stats)
        assert result is None
        assert center.has_warning is True

    def test_within_range_no_warning(self):
        rule = TemperatureWarningRule()
        center = make_center()
        stats = make_stats(min_temp=3.0, max_temp=7.0)
        result = rule.evaluate(center, stats)
        assert result is None
        assert center.has_warning is False


class TestThawRule:
    def test_not_ultra_cold_returns_none(self):
        rule = ThawRule()
        center = make_center(ultra_cold_chain_required=False)
        assert rule.evaluate(center, make_stats()) is None

    def test_no_thaw_start_returns_none(self):
        rule = ThawRule()
        center = make_center(ultra_cold_chain_required=True, thaw_start_time=None)
        assert rule.evaluate(center, make_stats()) is None

    def test_thaw_exceeded_returns_rejected(self):
        rule = ThawRule()
        old_date = (datetime.now() - timedelta(days=80)).strftime("%Y-%m-%d")
        center = make_center(
            ultra_cold_chain_required=True,
            thaw_start_time=old_date,
            thaw_duration_days=70,
        )
        assert rule.evaluate(center, make_stats()) == "REJECTED_THAW"

    def test_thaw_within_limit_logs_remaining(self):
        rule = ThawRule()
        recent_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        center = make_center(
            ultra_cold_chain_required=True,
            thaw_start_time=recent_date,
            thaw_duration_days=70,
        )
        result = rule.evaluate(center, make_stats())
        assert result is None
        assert any("متبقي" in r for r in center.decision_reasons)

    def test_invalid_thaw_date_returns_none(self):
        rule = ThawRule()
        center = make_center(
            ultra_cold_chain_required=True,
            thaw_start_time="invalid-date",
        )
        assert rule.evaluate(center, make_stats()) is None
