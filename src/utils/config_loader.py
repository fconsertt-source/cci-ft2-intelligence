import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    _config = None

    @classmethod
    def load(cls, config_path: str = "config/system_config.yaml") -> Dict[str, Any]:
        """Loads and caches the system configuration."""
        if cls._config is None:
            if not os.path.exists(config_path):
                # Fallback or default values if config is missing
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._config = yaml.safe_load(f)
        
        return cls._config

    @classmethod
    def get(cls, key_path: str, default: Any = None) -> Any:
        """
        Retrieves a nested key from the config using dot notation.
        Example: get("paths.fonts_dir")
        """
        config = cls.load()
        keys = key_path.split('.')
        
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
