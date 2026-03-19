from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.application.ports.ft2_reader_port import Ft2ReaderPort
from src.domain.dtos.ft2_entry_dto import FT2EntryDTO

logger = logging.getLogger(__name__)


class BerlingerFt2Reader(Ft2ReaderPort):
    """النسخة النهائية — تعمل مع التنسيق الحقيقي لـ Fridge-tag 2 E"""

    def read(self, source: str) -> List[FT2EntryDTO]:
        path = Path(source)
        if path.is_dir():
            entries = []
            for file_path in path.glob("*.txt"):
                entries.extend(self._parse_single_file(file_path))
            return entries
        return self._parse_single_file(path)

    def _parse_single_file(self, path: Path) -> List[FT2EntryDTO]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        device_id = re.search(r"Serial[:\s]*(\d+)", content)
        device_id = device_id.group(1) if device_id else "UNKNOWN"

        batch_id = path.stem
        center_id = (
            path.parent.name if path.parent.name != "input_ft2" else "TEST_CENTER_01"
        )

        entries = self._parse_hist_section(content, device_id, batch_id, center_id)
        logger.info(f"✅ تم استخراج {len(entries)} إدخال من {path.name}")
        return entries

    def _parse_hist_section(
        self, content: str, device_id: str, batch_id: str, center_id: str
    ) -> List[FT2EntryDTO]:
        entries = []
        lines = content.splitlines()
        in_hist = False
        current_day: Dict[str, str] = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("Hist"):
                in_hist = True
                continue

            if in_hist and any(x in line.lower() for x in ["conf", "alarm", "log"]):
                if current_day:
                    entries.extend(
                        self._create_entries(
                            current_day, device_id, batch_id, center_id
                        )
                    )
                break

            if in_hist:
                if line.startswith("Date:"):
                    if current_day:
                        entries.extend(
                            self._create_entries(
                                current_day, device_id, batch_id, center_id
                            )
                        )
                        current_day = {}
                    current_day["Date"] = line.split(":", 1)[1].strip()

                elif "Min T:" in line:
                    m = re.search(r"Min T:\s*([+-]?\d+\.?\d*)", line)
                    if m:
                        current_day["Min T"] = m.group(1)

                elif "Max T:" in line:
                    m = re.search(r"Max T:\s*([+-]?\d+\.?\d*)", line)
                    if m:
                        current_day["Max T"] = m.group(1)

                elif "Avrg T:" in line or "Avg T:" in line:
                    m = re.search(r"Avrg?\s*T:\s*([+-]?\d+\.?\d*)", line)
                    if m:
                        current_day["Avg T"] = m.group(1)

                elif "t Acc" in line:
                    m = re.search(r"t Acc[^:]*:\s*(\d{2}:\d{2})", line)
                    if m:
                        if "below" in line.lower() or "<" in line:
                            current_day["t Acc <"] = m.group(1)
                        else:
                            current_day["t Acc >"] = m.group(1)

        if current_day:
            entries.extend(
                self._create_entries(current_day, device_id, batch_id, center_id)
            )

        return entries

    def _create_entries(
        self, day: Dict[str, str], device_id: str, batch_id: str, center_id: str
    ) -> List[FT2EntryDTO]:
        try:
            date_str = day.get("Date", "")
            dt = (
                datetime.strptime(date_str, "%d.%m.%Y")
                if "." in date_str
                else datetime.fromisoformat(date_str)
            )

            min_t = float(day.get("Min T", 0))
            max_t = float(day.get("Max T", 0))
            avg_t = float(day.get("Avg T", 0))

            t_low = self._parse_duration(day.get("t Acc <", "00:00"))
            t_high = self._parse_duration(day.get("t Acc >", "00:00"))

            status = "ALARM" if (t_low > 0 or t_high > 0) else "OK"

            entries = []

            entries.append(
                FT2EntryDTO(
                    id=f"{device_id}_{dt.date()}_MIN",
                    device_id=device_id,
                    timestamp=dt,
                    temperature=min_t,
                    duration_minutes=float(t_low),
                    vaccine_type="General",
                    batch=f"FT2_MIN|{status}",
                    batch_id=batch_id,
                    center_id=center_id,
                )
            )

            entries.append(
                FT2EntryDTO(
                    id=f"{device_id}_{dt.date()}_MAX",
                    device_id=device_id,
                    timestamp=dt,
                    temperature=max_t,
                    duration_minutes=float(t_high),
                    vaccine_type="General",
                    batch=f"FT2_MAX|{status}",
                    batch_id=batch_id,
                    center_id=center_id,
                )
            )

            entries.append(
                FT2EntryDTO(
                    id=f"{device_id}_{dt.date()}_AVG",
                    device_id=device_id,
                    timestamp=dt,
                    temperature=avg_t,
                    duration_minutes=float(1440 - t_low - t_high),
                    vaccine_type="General",
                    batch=f"FT2_AVG|{status}",
                    batch_id=batch_id,
                    center_id=center_id,
                )
            )

            return entries
        except Exception as e:
            logger.warning(f"خطأ في إنشاء إدخالات اليوم: {e}")
            return []

    def _parse_duration(self, time_str: str) -> int:
        try:
            h, m = map(int, time_str.split(":"))
            return h * 60 + m
        except Exception:
            return 0
