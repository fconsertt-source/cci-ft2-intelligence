# src/infrastructure/utils/vaccine_library_loader.py

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.infrastructure.validators.vaccine_library_schema import validate_vaccine_library


def load_vaccine_library(library_path: str = "config/vaccine_library.yaml") -> Dict[str, Any]:
    path = Path(library_path)
    if not path.exists():
        return {"defaults": {}, "vaccines": {}, "metadata": {}}

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return validate_vaccine_library(data)


class VaccineLibraryLoader:
    """
    Loads vaccine definitions from the vaccine_library.yaml file.
    """

    _instance = None
    _library: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VaccineLibraryLoader()
            cls._instance._load_library()
        return cls._instance

    def _load_library(self):
        config_path = "config/vaccine_library.yaml"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self._library = data.get("vaccines", {})

    def get_vaccine_data(self, vaccine_id: str) -> Optional[Dict[str, Any]]:
        # Check by id if available
        for key, data in self._library.items():
            if data.get("id") == vaccine_id or key == vaccine_id:
                return data
        return None

    def list_vaccines(self) -> Dict[str, Any]:
        return self._library
