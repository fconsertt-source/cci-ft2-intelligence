# ft2_validator.py (مُحسّن)
from typing import List, Dict, Any
from src.ft2_reader.parser.ft2_parser import FT2Entry

class FT2Validator:
    @staticmethod
    def validate_temporal_consistency(entries: List[FT2Entry]) -> Dict[str, Any]:
        """التحقق من التسلسل الزمني للبيانات"""
        if len(entries) < 2:
            return {"status": "INSUFFICIENT_DATA", "gaps": []}
        
        entries = sorted(entries, key=lambda e: e.timestamp)
        gaps = []
        data_quality = "GOOD"
        
        for i in range(len(entries) - 1):
            t1 = entries[i].timestamp
            t2 = entries[i + 1].timestamp
            gap_minutes = (t2 - t1).total_seconds() / 60
            
            # فجوة كبيرة (أكثر من ساعتين بين القراءات)
            if gap_minutes > 120:
                gaps.append({
                    "from": t1.isoformat(),
                    "to": t2.isoformat(),
                    "minutes": gap_minutes
                })
                data_quality = "WITH_GAPS"
        
        return {
            "status": data_quality,
            "gaps": gaps,
            "total_entries": len(entries),
            "time_span_hours": (entries[-1].timestamp - entries[0].timestamp).total_seconds() / 3600
        }