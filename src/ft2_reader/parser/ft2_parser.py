import os
import csv
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FT2Entry:
    def __init__(self, device_id: str, timestamp: str, temperature: float, 
                 vaccine_type: str, batch: str, duration_minutes: float = 15.0):
        self.device_id = device_id
        self.timestamp = timestamp
        self.temperature = temperature
        self.vaccine_type = vaccine_type
        self.batch = batch
        self.duration_minutes = duration_minutes
    
    def __repr__(self):
        return f"FT2Entry(device={self.device_id}, temp={self.temperature}°C, time={self.timestamp})"

class FT2Parser:
    @staticmethod
    def parse_file(file_path: str) -> List[FT2Entry]:
        entries = []
        
        # دعم لكل من CSV و TSV
        delimiter = '\t' if file_path.endswith('.tsv') else ','
        
        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                # محاولة اكتشاف الرأس
                first_line = f.readline()
                f.seek(0)
                
                if 'device_id' in first_line and 'temperature' in first_line:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    for i, row in enumerate(reader):
                        try:
                            entry = FT2Entry(
                                device_id=str(row['device_id']),
                                timestamp=row.get('timestamp', datetime.now().isoformat()),
                                temperature=float(row['temperature']),
                                vaccine_type=row.get('vaccine_type', 'UNKNOWN'),
                                batch=row.get('batch', 'UNKNOWN'),
                                duration_minutes=15.0  # افتراض 15 دقيقة لكل قراءة في CSV
                            )
                            entries.append(entry)
                        except Exception as e:
                            logger.warning(f"تخطي صف {i} في {file_path}: {e}")
                else:
                    logger.warning(f"تنسيق غير معروف في {file_path}")
        
        except Exception as e:
            logger.error(f"خطأ في تحليل {file_path}: {e}")
        
        logger.info(f"تم تحليل {len(entries)} إدخال من {file_path}")
        return entries