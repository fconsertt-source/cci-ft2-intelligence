import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class SessionRegistry:
    """سجل زمني لكل جهاز - يمنع التكرار ويحافظ على الاستمرارية"""
    def __init__(self, registry_path: Path = Path("data/registry/session_registry.json")):
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict = self._load()

    def _load(self) -> Dict:
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text(encoding="utf-8"))
            except:
                return {}
        return {}

    def save(self):
        self.registry_path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def get_last_processed(self, device_id: str) -> Optional[datetime]:
        entry = self.data.get(device_id)
        if not entry or "last_timestamp" not in entry:
            return None
        return datetime.fromisoformat(entry["last_timestamp"])

    def mark_processed(self, device_id: str, last_timestamp: datetime, filename: str, readings_count: int):
        self.data[device_id] = {
            "last_timestamp": last_timestamp.isoformat(),
            "last_file": filename,
            "total_readings": self.data.get(device_id, {}).get("total_readings", 0) + readings_count,
            "updated_at": datetime.now().isoformat()
        }
        self.save()

    def is_new_data(self, device_id: str, file_timestamp: datetime) -> bool:
        """هل هذه البيانات جديدة ولم تُعالج من قبل؟"""
        last = self.get_last_processed(device_id)
        return last is None or file_timestamp > last
