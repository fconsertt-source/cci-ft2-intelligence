import os
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self._features = {
            'CCI_ENABLE_SUPPLY_DATE': os.getenv('CCI_ENABLE_SUPPLY_DATE', 'false').lower() == 'true',
            'CCI_ENABLE_HEAT_DURATION': os.getenv('CCI_ENABLE_HEAT_DURATION', 'false').lower() == 'true',
        }

    def get_feature(self, feature_name: str) -> bool:
        return self._features.get(feature_name, False)

    def set_feature(self, feature_name: str, enabled: bool) -> None:
        self._features[feature_name] = enabled

_config_instance = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
