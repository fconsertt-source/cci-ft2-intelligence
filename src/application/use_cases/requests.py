from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GenerateDeviceReportRequest:
    device_id: str
    operator: str = "system"
    cycle_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@dataclass
class EvaluateColdChainRequest:
    center_id: str
    cycle_id: str
    include_forecast: bool = False
