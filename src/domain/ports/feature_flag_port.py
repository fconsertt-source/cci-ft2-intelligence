from typing import Protocol

class FeatureFlagPort(Protocol):
    def is_enabled(self, flag_name: str) -> bool:
        ...
