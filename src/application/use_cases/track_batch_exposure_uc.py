from typing import List

from src.domain.value_objects.cumulative_exposure_result import \
    CumulativeExposureResult
from src.domain.value_objects.heat_exposure import HeatExposure


def execute(
    self, batch_id: str, exposures: List[HeatExposure]
) -> CumulativeExposureResult:
    """Accumulate exposure for a batch.

    Note: manufacture_date is set to current time on first appearance.
    This represents 'first seen in system' — NOT actual manufacturing date.
    Actual manufacturing date should be imported from external source when available.
    """
    ...
