from dataclasses import dataclass, field
from typing import List, Any

@dataclass(frozen=True)
class ValidationResult:
    """DTO for center mapping validation results."""
    is_ssot_valid: bool
    yaml_count: int
    affected_count: int
    unregistered_centers: List[Any] = field(default_factory=list)
    message: str = ""