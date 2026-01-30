"""Simple Composition Root / DI helpers.

This module provides factory functions to construct Use Cases and adapters
using explicit wiring. It is intentionally minimal — the goal is to centralize
construction so Presentation and Application do not `new` domain components.
"""
from typing import Optional

from src.application.use_cases.evaluate_cold_chain_safety_uc import EvaluateColdChainSafetyUC


def create_evaluate_cold_chain_uc(reader=None, repository=None) -> EvaluateColdChainSafetyUC:
    """Create an EvaluateColdChainSafetyUC with injected dependencies.

    If `reader` is None, callers should provide a concrete FT2 reader adapter.
    This helper centralizes wiring and can be extended to read configuration
    and construct real adapters.
    """
    return EvaluateColdChainSafetyUC(reader=reader, repository=repository)
