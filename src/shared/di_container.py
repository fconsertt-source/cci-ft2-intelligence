"""Simple Composition Root / DI helpers.

This module provides factory functions to construct Use Cases and adapters
using explicit wiring. It is intentionally minimal — the goal is to centralize
construction so Presentation and Application do not `new` domain components.
"""
from typing import Optional

from src.application.use_cases.evaluate_cold_chain_safety_uc import EvaluateColdChainSafetyUC
from src.infrastructure.adapters.ft2_repository_adapter import Ft2RepositoryAdapter
from src.infrastructure.adapters.noop_reporter_adapter import NoOpReporter


def create_evaluate_cold_chain_uc(reader=None, repository=None) -> EvaluateColdChainSafetyUC:
    """Backward-compatible factory. Prefer build_evaluate_uc for explicit wiring."""
    return EvaluateColdChainSafetyUC(reader=reader, repository=repository)


def build_evaluate_uc() -> EvaluateColdChainSafetyUC:
    """Explicit Composition Root wiring with concrete adapters.

    No conditional logic; this is the only place that sees infrastructure.
    """
    repo = Ft2RepositoryAdapter()
    reporter = NoOpReporter()  # Replace with real reporter (e.g., PdfReporter) when ready
    return EvaluateColdChainSafetyUC(repository=repo, reporter=reporter)
