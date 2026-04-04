# src/application/dtos/center_report_dto.py
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass(frozen=True)
class CenterReportDTO:
    """Immutable DTO for center report data."""
    center_id: str
    center_name: str
    total_devices: int
    safe_devices: int
    rejected_devices: int
    partial_devices: int
    devices: List[Dict[str, Any]] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validation after initialization."""
        if not self.center_id:
            raise ValueError("center_id cannot be empty")
        if self.total_devices < 0:
            raise ValueError("total_devices cannot be negative")
        if self.safe_devices + self.rejected_devices + self.partial_devices != self.total_devices:
            raise ValueError("Device counts do not sum to total_devices")