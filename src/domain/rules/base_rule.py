# src/domain/rules/base_rule.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseRule(ABC):
    """Abstract base class for all domain rules with safe evaluation."""

    @abstractmethod
    def evaluate(self, context: Any, stats: Dict[str, Any]) -> Optional[str]:
        """
        Evaluate the rule against the given context and stats.

        Args:
            context: The domain context (e.g., DomainCenterContext).
            stats: Additional statistics from analysis services.

        Returns:
            Optional decision string if the rule applies, None otherwise.
        """
        pass

    def safe_evaluate(self, context: Any, stats: Dict[str, Any]) -> Optional[str]:
        """
        Safe wrapper for evaluate that catches exceptions and logs them.

        Returns:
            The decision or None if an error occurred.
        """
        try:
            return self.evaluate(context, stats)
        except Exception as e:
            # Log the error (assuming logger is available)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error evaluating rule {self.__class__.__name__}: {e}")
            return None