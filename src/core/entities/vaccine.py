from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Vaccine:
    """
    كيان يمثل لقاحًا واحدًا وقواعد تحمله الحراري
    """
    id: str
    name: str
    full_loss_threshold_low: float
    full_loss_threshold_high: float
    shelf_life_days: int

    # (Temperature °C, Max exposure minutes)
    reference_table: List[Tuple[float, int]]
