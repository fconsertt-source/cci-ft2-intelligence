from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from src.domain.entities.heat_exposure import HeatExposure


@dataclass(frozen=True)
class CumulativeExposureResult:
    """Result of cumulative exposure calculation for a vaccine batch."""

    batch_id: str
    cumulative_her: float
    cumulative_ccm: float
    status: str  # SAFE, PARTIAL, DISCARD, NO_DATA


@dataclass(frozen=True)
class VaccineBatch:
    """Single batch of vaccines tracked across cold chain stages.

    Accumulates heat exposure across multiple devices/stages.
    Note: manufacture_date represents 'first seen in system' — NOT actual manufacturing date.
    Actual manufacturing date should be imported from external source when available.
    """

    batch_id: str
    vaccine_type: str
    manufacture_date: datetime
    exposure_history: List[HeatExposure] = field(default_factory=list)

    def accumulate_exposure(self) -> CumulativeExposureResult:
        """Calculate cumulative heat exposure across all stages."""
        if not self.exposure_history:
            return CumulativeExposureResult(
                batch_id=self.batch_id,
                cumulative_her=0.0,
                cumulative_ccm=0.0,
                status="NO_DATA",
            )

        # Simple accumulation (real implementation would use Q10 model)
        cumulative_her = sum(exp.her for exp in self.exposure_history)
        cumulative_ccm = sum(exp.ccm for exp in self.exposure_history)

        # Decision logic based on cumulative exposure
        if cumulative_her < 15.0:
            status = "SAFE"
        elif cumulative_her < 30.0:
            status = "PARTIAL"
        else:
            status = "DISCARD"

        return CumulativeExposureResult(
            batch_id=self.batch_id,
            cumulative_her=cumulative_her,
            cumulative_ccm=cumulative_ccm,
            status=status,
        )
