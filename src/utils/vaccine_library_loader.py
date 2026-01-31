import yaml
import os
from typing import Dict, Any, Optional

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
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self._library = data.get('vaccines', {})

    def get_vaccine_data(self, vaccine_id: str) -> Optional[Dict[str, Any]]:
        # Check by id if available
        for key, data in self._library.items():
            if data.get('id') == vaccine_id or key == vaccine_id:
                return data
        return None

    def list_vaccines(self) -> Dict[str, Any]:
        return self._library
