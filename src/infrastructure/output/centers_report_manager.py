import pandas as pd
from pathlib import Path
from datetime import datetime

class CentersReportManager:
    """تحديث آمن لملف centers_report.tsv بطريقة Upsert"""
    def __init__(self, tsv_path: Path):
        self.tsv_path = tsv_path

    def update_device(self, device_id: str, metrics: dict):
        metrics["device_id"] = device_id
        metrics["updated_at"] = datetime.now().isoformat()

        new_row = pd.DataFrame([metrics])

        if self.tsv_path.exists():
            df = pd.read_csv(self.tsv_path, sep="\t")
            df = df[df["device_id"] != device_id]
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = new_row

        df.sort_values("updated_at", inplace=True)
        df.to_csv(self.tsv_path, sep="\t", index=False, encoding="utf-8-sig")
