from __future__ import annotations

from src.application.ports.validation_protocol_port import \
    ValidationProtocolPort


class ValidationProtocolService(ValidationProtocolPort):
    """
    Provides validation protocols for different vaccine types.
    Enforces mandatory validation for PARTIAL status.
    """

    def get_protocol(self, vaccine_type: str) -> dict:
        """
        Returns: validation protocol for vaccine type.
        """
        # Default protocol for PARTIAL cases
        return {
            "required": True,
            "method": "Shake Test + Visual Inspection",
            "timeframe_hours": 24,
            "responsible": "Quality Control Officer",
            "documentation_required": True,
        }
