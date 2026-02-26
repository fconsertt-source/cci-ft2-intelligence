# src/domain/enums/safety_status.py (جديد)
from enum import Enum

class SafetyStatus(Enum):
    SAFE = "SAFE"
    PARTIAL = "PARTIAL" 
    DISCARD = "DISCARD"
    NO_DATA = "NO_DATA"