"""Verify that PDF strategies use the new engine when available."""

from src.infrastructure.adapters.reporting.pdf_strategy import (
    ArabicPDFStrategy, OfficialPDFStrategy, TechnicalPDFStrategy)
from src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper import \
    UnifiedPDFGeneratorWrapper


def test_strategies_use_wrapper():
    """Strategies should delegate to the unified wrapper (not the legacy engine)."""
    for strat_cls in (OfficialPDFStrategy, TechnicalPDFStrategy, ArabicPDFStrategy):
        strat = strat_cls()
        assert isinstance(
            strat.generator, UnifiedPDFGeneratorWrapper
        ), "Strategy must use wrapper"
