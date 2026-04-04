#!/usr/bin/env python3
"""
فخ التناقض المنطقي: اختب منطق SSOT.
"""
import sys
import os
sys.path.insert(0, '/home/amer11974/projects/cci-ft2-intelligence-clean/src')

from dataclasses import dataclass
from typing import List

@dataclass
class MockFT2Entry:
    pass

@dataclass
class MockEquipmentUnit:
    ft2_entries: List[MockFT2Entry]

@dataclass
class MockCenter:
    id: str
    equipment_units: List[MockEquipmentUnit]

# استيراد الدالة
from src.application.services.center_impact_service import CenterImpactService

def create_mock_data():
    # إنشاء 5 مراكز فريدة، لكن مع حقن مراكز مكررة لجعل affected_centers = 8
    centers = []
    # 5 مراكز فريدة
    for i in range(5):
        centers.append(MockCenter(id=f'center_{i}', equipment_units=[MockEquipmentUnit(ft2_entries=[MockFT2Entry()])]))
    # إضافة 3 مراكز مكررة أو وهمية لجعل العدد 8
    centers.append(MockCenter(id='center_0', equipment_units=[MockEquipmentUnit(ft2_entries=[MockFT2Entry()])]))  # مكرر
    centers.append(MockCenter(id='center_1', equipment_units=[MockEquipmentUnit(ft2_entries=[MockFT2Entry()])]))  # مكرر
    centers.append(MockCenter(id='center_2', equipment_units=[MockEquipmentUnit(ft2_entries=[MockFT2Entry()])]))  # مكرر
    return centers

def test_ssot():
    centers = create_mock_data()
    yaml_count = 5
    affected_count = CenterImpactService.count_affected_centers(centers)
    is_valid, message = CenterImpactService.verify_ssot(yaml_count, affected_count)
    print(f"yaml_count: {yaml_count}, affected_count: {affected_count}")
    print(f"is_valid: {is_valid}, message: {message}")
    if is_valid:
        print("المنطق خاطئ: يجب أن يكون False لأن 5 != 8")
        return False
    if '+3' not in message:
        print("الرسالة لا تحتوي على +3")
        return False
    return True

def test_empty_units():
    # مراكز مع equipment_units فارغة
    centers = [
        MockCenter(id='center_1', equipment_units=[]),
        MockCenter(id='center_2', equipment_units=[MockEquipmentUnit(ft2_entries=[])])
    ]
    count = CenterImpactService.count_affected_centers(centers)
    print(f"عدد المراكز المتأثرة مع وحدات فارغة: {count}")
    if count != 0:
        print("الدالة تحسب المراكز الفارغة، ليست ذكية")
        return False
    return True

if __name__ == "__main__":
    if not test_ssot():
        sys.exit(1)
    if not test_empty_units():
        sys.exit(1)
    print("المنطق صحيح")