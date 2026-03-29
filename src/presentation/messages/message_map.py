"""
Centralized message provider to prevent linguistic drift in user-facing text.
Design principle: Domain emits codes → Presentation maps to human-readable text.
All user-facing text MUST flow through this module.
"""

from typing import Any
from src.shared.language_manager import lang


class MessageProvider:
    """Centralized provider for all user-facing messages.

    Architectural contract:
      - Domain layer MUST return codes only (e.g., "ACCEPTED")
      - Presentation layer MUST map codes → text via this provider
      - NO hardcoded user messages allowed outside this module
    """

    CLI_DECISION_SYMBOLS = {
        "ACCEPTED": ("[+]", "green"),
        "WARNING": ("[!]", "yellow"),
        "REJECTED": ("[X]", "red"),
        "NO_DATA": ("[?]", "gray"),
    }

    @classmethod
    def get_decision_symbol(cls, decision: str) -> str:
        for key, (symbol, _) in cls.CLI_DECISION_SYMBOLS.items():
            if key in decision:
                return symbol
        return "[?]"

    @staticmethod
    def get(key: str, **kwargs: Any) -> str:
        """
        Retrieves and formats a message from the language manager.

        Args:
            key: Message key from translation files (e.g., 'VISUAL_REPORT_OFFICIAL')
            **kwargs: Values to substitute into message placeholders

        Returns:
            Formatted message string in the current language

        Guarantees:
          - Always returns a string (never raises for missing keys)
          - Graceful degradation on formatting errors
        """
        message = lang.get(key)
        if message is None:
            return f"⚠️ رسالة مفقودة: {key}"

        try:
            return message.format(**kwargs)
        except (KeyError, TypeError):
            return f"⚠️ خطأ تنسيق: {message}"


# Backward compatibility alias
MessageMap = MessageProvider
