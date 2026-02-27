#!/usr/bin/env python3
"""
استيراد/تصدير CSV للقاحات والوحدات

✅ يقلل الأخطاء البشرية
✅ يسرع إدخال البيانات
✅ قابل للتوسع
"""

import csv
from pathlib import Path
from typing import List, Dict


def export_vaccines_to_csv(vaccines: List[Dict], output_path: Path) -> None:
    """تصدير قائمة اللقاحات إلى CSV"""
    if not vaccines:
        return
    
    fieldnames = ['name', 'quantity', 'batch_number', 'production_date', 'expiry_date', 'notes']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(vaccines)


def import_vaccines_from_csv(input_path: Path) -> List[Dict]:
    """استيراد قائمة اللقاحات من CSV"""
    if not input_path.exists():
        raise FileNotFoundError(f"CSV file not found: {input_path}")
    
    vaccines = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vaccines.append(row)
    
    return vaccines


def validate_vaccine_data(vaccines: List[Dict]) -> List[str]:
    """التحقق من صحة بيانات اللقاحات"""
    errors = []
    
    for i, vaccine in enumerate(vaccines):
        if not vaccine.get('name'):
            errors.append(f"Row {i+1}: Vaccine name is required")
        if not vaccine.get('batch_number'):
            errors.append(f"Row {i+1}: Batch number is required")
    
    return errors
