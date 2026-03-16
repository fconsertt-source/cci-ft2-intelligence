#!/usr/bin/env python3
"""
FT2 Parser — Berlinger Fridge-tag 2 E
يستخرج البيانات اليومية من ملف .txt ويُنتج CSV جاهز للـ pipeline.

البنية المتوقعة:
    device_id, date, avg_temp, min_temp, max_temp,
    alarm_freeze_minutes, alarm_heat_minutes, has_freeze_alarm, has_heat_alarm

المصدر: تنسيق Hist في ملف Fridge-tag 2 E
"""

import csv
import re
from pathlib import Path
from typing import List, Optional


# ── ثوابت الجهاز (من ملف البيانات) ─────────────────────────────────────────
FREEZE_ALARM_THRESHOLD = -0.5   # °C — حد إنذار التجميد
HEAT_ALARM_THRESHOLD = 8.0      # °C — حد إنذار الحرارة
FREEZE_ALARM_DURATION_MIN = 60  # دقيقة — مدة تفعيل إنذار التجميد
HEAT_ALARM_DURATION_MIN = 600   # دقيقة — مدة تفعيل إنذار الحرارة


def parse_temp(value: str) -> Optional[float]:
    """تحويل قيمة درجة الحرارة من النص إلى float."""
    try:
        return float(value.replace("+", "").replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def parse_ft2_txt(file_path: Path) -> List[dict]:
    """
    استخراج البيانات اليومية من ملف Fridge-tag 2 E .txt

    Returns:
        قائمة من dicts — كل dict يمثل يوماً واحداً
    """
    content = file_path.read_text(encoding="utf-8", errors="replace")

    # استخراج device_id من اسم الملف أو من داخل الملف
    device_id = file_path.stem.split("_")[0] if "_" in file_path.stem else "unknown"

    # البحث عن device_id في محتوى الملف للتأكيد
    serial_match = re.search(r"Serial:\s*(\d+)", content)
    if serial_match:
        device_id = serial_match.group(1)

    records = []
    current_entry = {}
    current_date = None

    lines = content.splitlines()
    i = 0

    # نبحث عن قسم Hist
    in_hist = False
    in_entry = False

    while i < len(lines):
        line = lines[i].strip()

        # بداية قسم Hist
        if line == "Hist:":
            in_hist = True
            i += 1
            continue

        # نهاية قسم Hist عند Cert
        if line.startswith("Cert:"):
            break

        if not in_hist:
            i += 1
            continue

        # رقم الإدخال (يوم جديد)
        entry_match = re.match(r"^(\d+):$", line)
        if entry_match:
            # حفظ الإدخال السابق إذا كان مكتملاً
            if current_entry and current_date:
                records.append(current_entry)

            current_entry = {
                "device_id": device_id,
                "date": None,
                "avg_temp": None,
                "min_temp": None,
                "max_temp": None,
                "alarm_freeze_minutes": 0,
                "alarm_heat_minutes": 0,
                "has_freeze_alarm": False,
                "has_heat_alarm": False,
            }
            current_date = None
            in_entry = True
            i += 1
            continue

        if not in_entry:
            i += 1
            continue

        # التاريخ
        date_match = re.match(r"Date:\s*(\d{4}-\d{2}-\d{2})", line)
        if date_match:
            current_date = date_match.group(1)
            current_entry["date"] = current_date
            i += 1
            continue

        # متوسط درجة الحرارة
        avg_match = re.match(r"Avrg T:\s*([+-]?\d+\.?\d*)", line)
        if avg_match:
            current_entry["avg_temp"] = parse_temp(avg_match.group(1))
            i += 1
            continue

        # درجة الحرارة الدنيا
        min_match = re.match(r"Min T:\s*([+-]?\d+\.?\d*)", line)
        if min_match:
            current_entry["min_temp"] = parse_temp(min_match.group(1))
            i += 1
            continue

        # درجة الحرارة القصوى
        max_match = re.match(r"Max T:\s*([+-]?\d+\.?\d*)", line)
        if max_match:
            current_entry["max_temp"] = parse_temp(max_match.group(1))
            i += 1
            continue

        # تراكم وقت الإنذار — نحتاج السياق لمعرفة نوع الإنذار (0=freeze, 1=heat)
        # نتعقب موضع الإنذار الحالي
        if re.match(r"0:", line):
            # إنذار 0 = freeze (-0.5°C)
            j = i + 1
            while j < len(lines):
                inner = lines[j].strip()
                t_acc_match = re.match(r"t Acc:\s*(\d+)", inner)
                if t_acc_match:
                    minutes = int(t_acc_match.group(1))
                    current_entry["alarm_freeze_minutes"] = minutes
                    if minutes > 0:
                        current_entry["has_freeze_alarm"] = True
                    break
                if re.match(r"^\d+:$", inner) or inner.startswith("1:"):
                    break
                j += 1
            i += 1
            continue

        if re.match(r"1:", line):
            # إنذار 1 = heat (+8.0°C)
            j = i + 1
            while j < len(lines):
                inner = lines[j].strip()
                t_acc_match = re.match(r"t Acc:\s*(\d+)", inner)
                if t_acc_match:
                    minutes = int(t_acc_match.group(1))
                    current_entry["alarm_heat_minutes"] = minutes
                    if minutes > 0:
                        current_entry["has_heat_alarm"] = True
                    break
                if re.match(r"^\d+:$", inner):
                    break
                j += 1
            i += 1
            continue

        i += 1

    # حفظ آخر إدخال
    if current_entry and current_date:
        records.append(current_entry)

    return records


def extract_and_convert(input_path: Path, output_path: Path) -> int:
    """
    استخراج البيانات من .txt وكتابتها كـ CSV.

    Returns:
        عدد السجلات المُستخرَجة
    """
    records = parse_ft2_txt(input_path)

    if not records:
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "device_id", "date", "avg_temp", "min_temp", "max_temp",
        "alarm_freeze_minutes", "alarm_heat_minutes",
        "has_freeze_alarm", "has_heat_alarm",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return len(records)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python ft2_txt_parser.py <input.txt> <output.csv>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    count = extract_and_convert(input_file, output_file)
    print(f"✅ استُخرج {count} سجل → {output_file}")