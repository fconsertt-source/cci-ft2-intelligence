# src/infrastructure/adapters/processed_csv_reader.py
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set

from src.domain.dtos.ft2_entry_dto import FT2EntryDTO

logger = logging.getLogger(__name__)


class ProcessedCsvReader:
    """قارئ لملفات CSV المعالجة (المخرجات اليومية)"""

    def read(self, source: str) -> List[FT2EntryDTO]:
        path = Path(source)
        entries = []
        device_ids_found: Set[str] = set()

        logger.info(f"📄 قراءة CSV المعالج: {path.name}")

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row_count = 0

            for row in reader:
                row_count += 1
                device_id = row.get("device_id", "").strip()

                if device_id:
                    device_ids_found.add(device_id)

                # تحويل التاريخ
                date_str = row.get("date", "")
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"⚠️ تاريخ غير صالح في السطر {row_count}: {date_str}")
                    continue

                base_id = f"{device_id}_{dt.strftime('%Y%m%d')}"

                # إنشاء 3 إدخالات للتوافق مع FT2 (MIN, MAX, AVG)
                # 1. MIN
                entries.append(
                    FT2EntryDTO(
                        id=f"{base_id}_MIN",
                        device_id=device_id,
                        timestamp=dt,
                        temperature=float(row.get("min_temp", 0) or 0),
                        duration_minutes=0,
                        vaccine_type="General",
                        batch=f"CSV_MIN|{'ALARM' if row.get('has_freeze_alarm') == 'True' else 'OK'}",
                        batch_id=path.stem,
                        center_id="AUTO",
                    )
                )

                # 2. MAX
                entries.append(
                    FT2EntryDTO(
                        id=f"{base_id}_MAX",
                        device_id=device_id,
                        timestamp=dt,
                        temperature=float(row.get("max_temp", 0) or 0),
                        duration_minutes=0,
                        vaccine_type="General",
                        batch=f"CSV_MAX|{'ALARM' if row.get('has_heat_alarm') == 'True' else 'OK'}",
                        batch_id=path.stem,
                        center_id="AUTO",
                    )
                )

                # 3. AVG (الرئيسي)
                entries.append(
                    FT2EntryDTO(
                        id=f"{base_id}_AVG",
                        device_id=device_id,
                        timestamp=dt,
                        temperature=float(row.get("avg_temp", 0) or 0),
                        duration_minutes=1440,  # يوم كامل
                        vaccine_type="General",
                        batch="CSV_AVG|OK",
                        batch_id=path.stem,
                        center_id="AUTO",
                    )
                )

        logger.info(f"✅ تم استخراج {len(entries)} إدخال من {row_count} يوم")
        logger.info(f"🔍 الأجهزة المfoundة: {device_ids_found}")

        return entries
