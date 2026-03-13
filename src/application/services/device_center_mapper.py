from __future__ import annotations
import yaml
from typing import Optional, Dict

class DeviceCenterMapper:
    """Contextual enrichment service — maps physical devices to administrative centers.
    
    Responsibilities:
      ✅ Load mapping from external file
      ✅ Return administrative context for a device
      ✅ Fail-safe: return None if mapping not found
    
    Boundaries:
      ❌ NO business logic
      ❌ NO decision making
      ❌ NO assumptions about device state
    """
    
    def __init__(self, mapping_file: str = "config/device_center_mapping.yaml"):
        self.mapping: Dict[str, Dict] = self._load_mapping(mapping_file)
    
    def _load_mapping(self, path: str) -> Dict[str, Dict]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('device_center_map', {})
        except FileNotFoundError:
            return {}  # ← Fail-safe: no mapping = no context
    
    def get_center_context(self, device_id: str) -> Optional[Dict]:
        """Returns administrative context for a device — or None if not mapped."""
        return self.mapping.get(device_id)