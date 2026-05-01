from __future__ import annotations

from typing import Dict, Any


class ReconcileLegacyVsReferenceUseCase:
    """
    Reconciles legacy exposure analysis with the new parallel scientific reference audit.
    """

    def execute(self, legacy_stats: Dict[str, Any], reference_audit: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "legacy_her_ratio": legacy_stats.get("her_ratio", 0.0),
            "reference_her_ratio": reference_audit.get("reference_her_ratio", 0.0),
            "her_ratio_delta": reference_audit.get("reference_her_ratio", 0.0) - legacy_stats.get("her_ratio", 0.0),
            "reference_mkt_c": reference_audit.get("reference_mkt_c"),
            "reference_source": reference_audit.get("reference_source"),
            "audit_enabled": reference_audit.get("reference_audit_enabled", False),
            "requires_reconciliation_review": abs(
                reference_audit.get("reference_her_ratio", 0.0) - legacy_stats.get("her_ratio", 0.0)
            ) > 0.05,
        }
