from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class FT2EntryDTO:
    """Represents a single temperature reading with full contextual awareness.
    
    Fields device_id, batch_id, and center_id enable hierarchical analysis:
      - device_id: Physical device (from Serial field in FT2 file)
      - batch_id: Vaccine batch (extracted from filename)
      - center_id: Administrative center (extracted from parent directory)
    """
    id: str
    device_id: str
    timestamp: datetime
    temperature: float
    vaccine_type: str
    batch: str
    duration_minutes: float
    
    # New optional fields for hierarchical analysis (Phase 5)
    batch_id: str = "UNKNOWN"      # ← Optional: extracted from filename
    center_id: str = "UNKNOWN"     # ← Optional: extracted from directory name
