# src/application/use_cases/track_batch_exposure_uc.py
def execute(self, batch_id: str, exposures: List[HeatExposure]) -> CumulativeExposureResult:
    """Accumulate exposure for a batch.
    
    Note: manufacture_date is set to current time on first appearance.
    This represents 'first seen in system' — NOT actual manufacturing date.
    Actual manufacturing date should be imported from external source when available.
    """
    ...