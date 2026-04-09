# src/infrastructure/utils/config_loader.py

import os
from typing import Any, Dict

import yaml


class ConfigLoader:
    _config = None

    @classmethod
    def load(cls, config_path: str = "config/system_config.yaml") -> Dict[str, Any]:
        """Loads and caches the system configuration."""
        if cls._config is None:
            if not os.path.exists(config_path):
                cls._config = {}
            else:
                with open(config_path, "r", encoding="utf-8") as f:
                    cls._config = yaml.safe_load(f) or {}

            cls._merge_thresholds()

        return cls._config

    @classmethod
    def _merge_thresholds(cls) -> None:
        """Merge threshold values from config/thresholds.yaml into the main config."""
        thresholds_path = "config/thresholds.yaml"
        if not os.path.exists(thresholds_path):
            return

        with open(thresholds_path, "r", encoding="utf-8") as f:
            thresholds_data = yaml.safe_load(f) or {}

        thresholds = thresholds_data.get("thresholds", {})
        if thresholds:
            cls._config.setdefault("thresholds", {})
            cls._config["thresholds"] = {
                **thresholds,
                **cls._config.get("thresholds", {}),
            }

    @classmethod
    def get(cls, key_path: str, default: Any = None) -> Any:
        """
        Retrieves a nested key from the config using dot notation.
        Example: get("paths.fonts_dir")
        """
        config = cls.load()
        keys = key_path.split(".")

        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
