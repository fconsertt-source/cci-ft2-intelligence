import pandas as pd
from datetime import timedelta

class ColdChainContinuityValidator:
    """يكشف الفجوات الزمنية الحرجة التي قد تؤثر على دقة HER/VVM/CCM"""
    MAX_GAP = timedelta(hours=2)

    @classmethod
    def validate(cls, df: pd.DataFrame, device_id: str) -> dict:
        if len(df) < 2:
            return {"valid": True, "gaps": [], "warning": "بيانات قليلة"}

        df = df.sort_values("timestamp")
        gaps = df["timestamp"].diff().dropna()
        critical_gaps = gaps[gaps > cls.MAX_GAP]

        if critical_gaps.empty:
            return {"valid": True, "gaps": [], "warning": None}

        return {
            "valid": False,
            "gaps": [{"start": idx, "duration_hours": gap.total_seconds()/3600} 
                     for idx, gap in critical_gaps.items()],
            "warning": f"توجد فجوات زمنية حرجة في جهاز {device_id} قد تؤثر على دقة الحسابات"
        }
