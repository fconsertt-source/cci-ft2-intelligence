from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ColdChainGap:
    start: object
    duration_hours: float


@dataclass(frozen=True)
class ColdChainAnalysisResult:
    valid: bool
    gaps: List[ColdChainGap]
    warning: Optional[str] = None
