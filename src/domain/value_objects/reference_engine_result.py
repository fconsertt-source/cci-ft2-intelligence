from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ReferenceEngineResult:
    vaccine_type: str
    her_ratio: float
    mkt_c: float
    ea_kj_mol: float
    reference_temp_c: float
    shelf_life_days: float
    rationale: str
    source: str
    traceability: Dict[str, Optional[str]]
    active: bool = True
