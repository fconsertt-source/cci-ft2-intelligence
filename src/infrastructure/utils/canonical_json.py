import json
from typing import Any


def to_canonical_json(obj: Any) -> str:
    """
    Serialize any object to canonical JSON for deterministic hashing.
    
    Features:
    - Sorted keys
    - Minimal separators (no whitespace)
    - UTF-8 encoding preserved
    - Consistent float representation
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        default=str  # Handle datetime, Path, etc.
    )