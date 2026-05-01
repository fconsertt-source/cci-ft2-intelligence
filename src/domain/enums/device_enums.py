from enum import Enum


class ReportDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED_HEAT_C = "REJECTED_HEAT_C"
    REJECTED_FREEZE = "REJECTED_FREEZE"
    REJECTED_EXPIRED = "REJECTED_EXPIRED"
    REJECTED_THAW = "REJECTED_THAW"
    PARTIAL = "PARTIAL"
    SAFE = "SAFE"
    UNKNOWN = "UNKNOWN"


class VVMStage(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
