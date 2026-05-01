from src.shared.config import get_config
from src.domain.ports.feature_flag_port import FeatureFlagPort

class FeatureFlagService(FeatureFlagPort):
    def __init__(self):
        self._config = get_config()

    def is_enabled(self, flag_name: str) -> bool:
        return self._config.get_feature(flag_name)
