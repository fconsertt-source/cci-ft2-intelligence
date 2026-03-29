#!/usr/bin/env python3
# scripts/preprocess_ft2.py
import os
import re
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# إضافة المسار إلى src
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Parser
from src.infrastructure.utils.yaml_loader import load_yaml, save_yaml
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

# المسارات
INPUT_FT2_DIR = "data/input_ft2"
INPUT_RAW_DIR = "data/input_raw"
CONFIG_PATH = "config/center_profiles.yaml"
PROCESSED_DIR = os.path.join(INPUT_FT2_DIR, "processed")

def extract_device_id(filename: str) -> str:
    """استخراج معرف الجهاز من اسم الملف (قبل أول شرطة سفلية)"""
    return filename.split('_')[0]

def get_existing_device_ids(config: dict) -> Set[str]:
    """جمع جميع معرفات الأجهزة الموجودة في YAML"""
    device_ids = set()
    centers = config.get('centers', {})
    for center_data in centers.values():
        equipment = center_data.get('equipment', {})
        for eq in equipment.values():
            if 'device_id' in eq:
                device_ids.add(eq['device_id'])
    return device_ids

def find_new_devices(files: List[str], existing_ids: Set[str]) -> Set[str]:
    """البحث عن أجهزة جديدة في ملفات input_ft2"""
    new = set()
    for f in files:
        if f.endswith(('.pdf', '.txt')):
            device_id = extract_device_id(f)
            if device_id not in existing_ids:
                new.add(device_id)
    return new

def parse_qtag_text(content: str, device_id: str) -> List[dict]:
    import re
    records = []
    hist_match = re.search(r'Hist:\s*\n(.*?)(?=\nCert:|$)', content, re.DOTALL)
    if not hist_match:
        return records

    hist_text = hist_match.group(1)
    lines = hist_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r'^\d+:$', line):
            record = {'device_id': device_id}
            i += 1
            block_lines = []
            while i < len(lines):
                next_line = lines[i].strip()
                if re.match(r'^\d+:$', next_line):
                    break
                block_lines.append(lines[i])
                i += 1
            block = "\n".join(block_lines)

            date_match = re.search(r'Date:\s*([\d-]+)', block)
            if not date_match:
                continue
            record['timestamp'] = date_match.group(1)

            avg_match = re.search(r'Avrg T:\s*([+\-]?\d+\.?\d*)', block)
            if avg_match:
                record['avg_temp'] = float(avg_match.group(1))

            freeze_acc = 0
            heat_acc = 0
            alarm_section = re.search(r'Alarm:\s*\n(.*?)(?=\n\s*\d+:|$)', block, re.DOTALL)
            if alarm_section:
                alarm_text = alarm_section.group(1)
                freeze_match = re.search(r'0:\s*\n\s*t Acc:\s*(\d+)', alarm_text)
                if freeze_match:
                    freeze_acc = int(freeze_match.group(1))
                heat_match = re.search(r'1:\s*\n\s*t Acc:\s*(\d+)', alarm_text)
                if heat_match:
                    heat_acc = int(heat_match.group(1))

            record['freeze_duration'] = freeze_acc
            record['heat_duration'] = heat_acc

            if 'timestamp' in record and 'avg_temp' in record:
                records.append(record)
        else:
            i += 1
    return records

def convert_text_to_csv(file_path: str, device_id: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"خطأ في قراءة الملف {file_path}: {e}")
        return None

    # اكتشاف Q‑tag
    if 'Hist:' in content and 'Avrg T:' in content:
        records = parse_qtag_text(content, device_id)
        if not records:
            logger.warning(f"لم يتم العثور على بيانات صالحة في Q‑tag {file_path}")
            return None

        csv_lines = []
        for rec in records:
            dt = rec['timestamp']
            try:
                dt_iso = datetime.strptime(dt, '%Y-%m-%d').isoformat()
            except:
                dt_iso = dt
            avg = rec.get('avg_temp', 0.0)
            freeze_dur = rec.get('freeze_duration', 0)
            heat_dur = rec.get('heat_duration', 0)
            row = f"{device_id},{dt_iso},{avg},UNKNOWN,UNKNOWN,1440,{freeze_dur},{heat_dur}"
            csv_lines.append(row)

        csv_name = f"{device_id}_converted.csv"
        csv_path = os.path.join(INPUT_RAW_DIR, csv_name)

        # حذف الملف الهدف إذا كان موجودًا
        if os.path.exists(csv_path):
            try:
                os.remove(csv_path)
            except Exception as e:
                logger.error(f"لا يمكن حذف الملف الموجود {csv_path}: {e}")
                return None

        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("device_id,timestamp,temperature,vaccine_type,batch,duration_minutes,freeze_duration,heat_duration\n")
            f.write("\n".join(csv_lines))
        logger.info(f"✅ تم تحويل Q‑tag {file_path} إلى {csv_path} ({len(records)} يوم)")
        return csv_path

    # النمط القديم (سطر سطر)
    lines = content.splitlines()
    csv_lines = []
    pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+([\d\.\-]+)\s+(\w+)\s+(\w+)'
    )
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = pattern.search(line)
        if match:
            ts, temp, vtype, batch = match.groups()
            csv_lines.append(f"{device_id},{ts},{temp},{vtype},{batch},15.0,0,0")
        else:
            logger.warning(f"تنسيق غير معروف في {file_path}: {line}")

    if not csv_lines:
        logger.warning(f"لم يتم العثور على بيانات صالحة في {file_path}")
        return None

    csv_name = f"{device_id}_converted.csv"
    csv_path = os.path.join(INPUT_RAW_DIR, csv_name)

    # حذف الملف الهدف إذا كان موجودًا
    if os.path.exists(csv_path):
        try:
            os.remove(csv_path)
        except Exception as e:
            logger.error(f"لا يمكن حذف الملف الموجود {csv_path}: {e}")
            return None

    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("device_id,timestamp,temperature,vaccine_type,batch,duration_minutes,freeze_duration,heat_duration\n")
        f.write("\n".join(csv_lines))
    logger.info(f"✅ تم تحويل {file_path} إلى {csv_path}")
    return csv_path

def convert_pdf_to_csv(file_path: str, device_id: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("مكتبة pypdf غير مثبتة. قم بتشغيل: pip install pypdf")
        return None

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        logger.error(f"خطأ في قراءة PDF {file_path}: {e}")
        return None

    logger.debug(f"Extracted text from {file_path}: {text[:1000]}...")

    # محاولة اكتشاف Q-tag
    if 'Hist:' in text and 'Avrg T:' in text:
        records = parse_qtag_text(text, device_id)

        if not records:
            logger.warning(f"لم يتم العثور على بيانات صالحة في Q-tag PDF {file_path}")
            return None

        csv_lines = []
        for rec in records:
            dt = rec['timestamp']
            try:
                dt_iso = datetime.strptime(dt, '%Y-%m-%d').isoformat()
            except Exception:
                dt_iso = dt

            avg = rec.get('avg_temp', 0.0)
            freeze_dur = rec.get('freeze_duration', 0)
            heat_dur = rec.get('heat_duration', 0)

            row = f"{device_id},{dt_iso},{avg},UNKNOWN,UNKNOWN,1440,{freeze_dur},{heat_dur}"
            csv_lines.append(row)

    else:
        # fallback parsing
        lines = text.splitlines()
        csv_lines = []

        pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+([\d\.\-]+)\s+(\w+)\s+(\w+)'
        )

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = pattern.search(line)
            if match:
                ts, temp, vtype, batch = match.groups()
                csv_lines.append(f"{device_id},{ts},{temp},{vtype},{batch},15.0,0,0")

        if not csv_lines:
            logger.warning(f"لم يتم العثور على بيانات صالحة في PDF {file_path}")
            return None

    csv_name = f"{device_id}_converted.csv"
    csv_path = os.path.join(INPUT_RAW_DIR, csv_name)

    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("device_id,timestamp,temperature,vaccine_type,batch,duration_minutes,freeze_duration,heat_duration\n")
        f.write("\n".join(csv_lines))

    logger.info(f"✅ تم تحويل PDF {file_path} إلى {csv_path}")
    return csv_path

def interactive_binding(new_device_ids: Set[str], config: dict) -> dict:
    """تفاعل مع المستخدم لربط الأجهزة الجديدة وتحديث التكوين"""
    centers = config.setdefault('centers', {})

    for device_id in sorted(new_device_ids):
        print(f"\n🔍 جهاز جديد: {device_id}")
        print("اختر:")
        print("  1. ربطه بمركز موجود")
        print("  2. إنشاء مركز جديد")
        print("  3. تخطي (لا تعالج)")
        choice = input("> ").strip()

        if choice == '1':
            center_names = list(centers.keys())
            if not center_names:
                print("لا يوجد مراكز. سيتحول إلى إنشاء مركز جديد.")
                choice = '2'
            else:
                print("المراكز الموجودة:")
                for i, name in enumerate(center_names, 1):
                    print(f"  {i}. {name}")
                idx = input(f"اختر رقم المركز (1-{len(center_names)}): ").strip()
                try:
                    center_name = center_names[int(idx) - 1]
                except (ValueError, IndexError):
                    print("إدخال غير صالح، تخطي.")
                    continue

                equipment_name = input("اسم المعدة (مثل 'غرفة تبريد'): ").strip()
                if not equipment_name:
                    equipment_name = f"جهاز {device_id}"

                centers[center_name].setdefault('equipment', {})[f"Device_{device_id}"] = {
                    'name': equipment_name,
                    'device_id': device_id
                }
                print(f"✅ تم ربط الجهاز {device_id} بالمركز '{center_name}' كمعدة '{equipment_name}'")
                continue

        if choice == '2':
            center_name = input("اسم المركز الجديد: ").strip()
            if not center_name:
                center_name = f"مركز {device_id}"
            equipment_name = input("اسم المعدة (مثل 'غرفة تبريد'): ").strip()
            if not equipment_name:
                equipment_name = f"جهاز {device_id}"

            centers[center_name] = {
                'name': center_name,
                'equipment': {
                    f"Device_{device_id}": {
                        'name': equipment_name,
                        'device_id': device_id
                    }
                }
            }
            print(f"✅ تم إنشاء مركز '{center_name}' مع الجهاز {device_id} كمعدة '{equipment_name}'")
            continue

        print(f"تخطي الجهاز {device_id}")

    return config

def convert_ft2_files_to_csv(ft2_files: List[str]) -> List[str]:
    converted = []
    for f in ft2_files:
        if not f.endswith(('.pdf', '.txt')):
            continue
        device_id = extract_device_id(f)
        file_path = os.path.join(INPUT_FT2_DIR, f)
        csv_path = None
        if f.endswith('.txt'):
            csv_path = convert_text_to_csv(file_path, device_id)
        # PDF files are not supported for conversion, skip them
        elif f.endswith('.pdf'):
            logger.info(f"تجاهل ملف PDF {f} - لا يدعم التحويل حالياً")
            continue

        if csv_path:
            converted.append(csv_path)
            os.makedirs(PROCESSED_DIR, exist_ok=True)
            shutil.move(file_path, os.path.join(PROCESSED_DIR, f))
            logger.info(f"📦 تم نقل {f} إلى {PROCESSED_DIR}/")
        else:
            logger.warning(f"فشل تحويل {f}")
    return converted

def main():
    # 1. التأكد من وجود المجلدات
    os.makedirs(INPUT_FT2_DIR, exist_ok=True)
    os.makedirs(INPUT_RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # 2. تحميل التكوين الحالي
    if os.path.exists(CONFIG_PATH):
        config = load_yaml(CONFIG_PATH)
    else:
        config = {'centers': {}}

    # 3. جمع ملفات input_ft2
    all_files = os.listdir(INPUT_FT2_DIR)
    
    # استبعاد مجلد processed نفسه إذا وجد
    ft2_files = [f for f in all_files if f.endswith(('.pdf', '.txt')) and not f.startswith('processed')]

    # استبعاد الملفات التي تمت معالجتها سابقاً
    if os.path.exists(PROCESSED_DIR):
        processed_files = set(os.listdir(PROCESSED_DIR))
        ft2_files = [f for f in ft2_files if f not in processed_files]

    if not ft2_files:
        logger.info("لا توجد ملفات PDF/TXT جديدة في input_ft2.")
        return

    # 4. معرفات الأجهزة الموجودة
    existing_ids = get_existing_device_ids(config)

    # 5. اكتشاف الأجهزة الجديدة
    new_ids = find_new_devices(ft2_files, existing_ids)

    if new_ids:
        print(f"\n🆕 تم العثور على {len(new_ids)} جهاز(ة) جديد(ة): {', '.join(new_ids)}")
        config = interactive_binding(new_ids, config)
        # حفظ التكوين المحدث
        save_yaml(config, CONFIG_PATH)
        print(f"✅ تم تحديث {CONFIG_PATH}")
    else:
        logger.info("لا توجد أجهزة جديدة.")

    # 6. تحويل الملفات إلى CSV (للأجهزة الجديدة فقط)
    converted_files = convert_ft2_files_to_csv(ft2_files)
    if converted_files:
        logger.info(f"تم تحويل {len(converted_files)} ملف(ات) إلى CSV في {INPUT_RAW_DIR}")
    else:
        logger.info("لا توجد ملفات تم تحويلها.")

    # 7. تشغيل pipeline الأساسي
    logger.info("🚀 تشغيل pipeline الأساسي...")
    from scripts.run_ft2_pipeline import run_pipeline
    run_pipeline(
        config_path=CONFIG_PATH,
        input_dir=INPUT_RAW_DIR,
        output_dir="data/output"
    )

if __name__ == "__main__":
    main()