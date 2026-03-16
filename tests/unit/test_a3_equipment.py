# tests/unit/test_a3_equipment.py
"""
اختبارات A3 — EquipmentRecord + DeviceCenterMapper المحدَّث

تغطية:
  1. EquipmentRecord — إنشاء، تحقق، تسلسل
  2. DeviceCenterMapper — تحميل YAML، استعلامات، توافق رجعي
  3. التكامل بين equipment_id و center_id و device_id
"""
from __future__ import annotations


import pytest
import yaml

from src.domain.entities.equipment_record import EquipmentRecord, EquipmentType
from src.application.services.device_center_mapper import DeviceCenterMapper


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════

SAMPLE_MAPPING = {
    "device_center_map": {
        "130600113437": {
            "center_id": "TEST_CENTER_01",
            "equipment_id": "EQ-FRIDGE-01",
            "equipment_type": "REFRIGERATOR",
            "location_note": "الثلاجة الرئيسية",
            "status": "ACTIVE",
        },
        "DEVICE_002": {
            "center_id": "CENTER_TRIPOLI_01",
            "equipment_id": "EQ-FRIDGE-02",
            "equipment_type": "REFRIGERATOR",
            "status": "ACTIVE",
        },
        "DEVICE_003": {
            "center_id": "CENTER_TRIPOLI_01",
            "equipment_id": "EQ-COLDROOM-01",
            "equipment_type": "COLD_ROOM",
            "status": "ACTIVE",
        },
    },
    "equipment_registry": {
        "EQ-FRIDGE-01": {
            "center_id": "TEST_CENTER_01",
            "equipment_type": "REFRIGERATOR",
            "capacity_liters": 120.0,
            "location_note": "الثلاجة الرئيسية",
        },
        "EQ-COLDROOM-01": {
            "center_id": "CENTER_TRIPOLI_01",
            "equipment_type": "COLD_ROOM",
            "capacity_liters": 2000.0,
        },
    },
}


@pytest.fixture
def mapping_file(tmp_path) -> str:
    """ملف YAML مؤقت للاختبارات."""
    path = tmp_path / "device_center_mapping.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(SAMPLE_MAPPING, f, allow_unicode=True)
    return str(path)


@pytest.fixture
def mapper(mapping_file) -> DeviceCenterMapper:
    return DeviceCenterMapper(mapping_file=mapping_file)


# ══════════════════════════════════════════════════════════════
# 1. اختبارات EquipmentRecord
# ══════════════════════════════════════════════════════════════

class TestEquipmentRecord:

    def test_create_basic(self):
        eq = EquipmentRecord(
            equipment_id="EQ-001",
            center_id="CTR-001",
        )
        assert eq.equipment_id == "EQ-001"
        assert eq.center_id == "CTR-001"
        assert eq.equipment_type == EquipmentType.REFRIGERATOR
        assert eq.active_device_id is None

    def test_equipment_types(self):
        for eq_type in EquipmentType:
            eq = EquipmentRecord(
                equipment_id="EQ-001",
                center_id="CTR-001",
                equipment_type=eq_type,
            )
            assert eq.equipment_type == eq_type

    def test_empty_equipment_id_raises(self):
        with pytest.raises(ValueError, match="equipment_id"):
            EquipmentRecord(equipment_id="", center_id="CTR-001")

    def test_empty_center_id_raises(self):
        with pytest.raises(ValueError, match="center_id"):
            EquipmentRecord(equipment_id="EQ-001", center_id="")

    def test_with_active_device_returns_new_instance(self):
        """with_active_device يعيد نسخة جديدة (immutable)."""
        eq = EquipmentRecord(equipment_id="EQ-001", center_id="CTR-001")
        eq2 = eq.with_active_device("DEV-123")

        assert eq2.active_device_id == "DEV-123"
        assert eq.active_device_id is None  # الأصل لم يتغير

    def test_immutable_after_creation(self):
        eq = EquipmentRecord(equipment_id="EQ-001", center_id="CTR-001")
        with pytest.raises((AttributeError, TypeError)):
            eq.equipment_id = "NEW-ID"

    def test_serialization_roundtrip(self):
        original = EquipmentRecord(
            equipment_id="EQ-001",
            center_id="CTR-001",
            equipment_type=EquipmentType.COLD_ROOM,
            location_note="غرفة التبريد",
            active_device_id="DEV-001",
            capacity_liters=500.0,
        )
        restored = EquipmentRecord.from_dict(original.to_dict())

        assert restored.equipment_id == original.equipment_id
        assert restored.center_id == original.center_id
        assert restored.equipment_type == original.equipment_type
        assert restored.location_note == original.location_note
        assert restored.active_device_id == original.active_device_id
        assert restored.capacity_liters == original.capacity_liters

    def test_str_representation(self):
        eq = EquipmentRecord(
            equipment_id="EQ-001",
            center_id="CTR-001",
            active_device_id="DEV-123",
        )
        text = str(eq)
        assert "EQ-001" in text
        assert "CTR-001" in text
        assert "DEV-123" in text


# ══════════════════════════════════════════════════════════════
# 2. اختبارات DeviceCenterMapper المحدَّث
# ══════════════════════════════════════════════════════════════

class TestDeviceCenterMapper:

    # ── التحميل ───────────────────────────────────────────────

    def test_loads_mapping_file(self, mapper):
        assert mapper.is_mapped("130600113437")
        assert mapper.is_mapped("DEVICE_002")

    def test_missing_file_no_crash(self, tmp_path):
        """ملف غير موجود → لا crash، mapper فارغ."""
        mapper = DeviceCenterMapper(
            mapping_file=str(tmp_path / "nonexistent.yaml")
        )
        assert mapper.get_center_context("ANY") is None

    # ── get_center_context (توافق رجعي) ───────────────────────

    def test_get_center_context_returns_center_id(self, mapper):
        """التوافق الرجعي: center_id لا يزال في السياق."""
        ctx = mapper.get_center_context("130600113437")
        assert ctx is not None
        assert ctx["center_id"] == "TEST_CENTER_01"

    def test_get_center_context_returns_equipment_id(self, mapper):
        """الجديد في A3: equipment_id موجود في السياق."""
        ctx = mapper.get_center_context("130600113437")
        assert ctx["equipment_id"] == "EQ-FRIDGE-01"

    def test_get_center_context_returns_equipment_type(self, mapper):
        ctx = mapper.get_center_context("130600113437")
        assert ctx["equipment_type"] == "REFRIGERATOR"

    def test_get_center_context_returns_location_note(self, mapper):
        ctx = mapper.get_center_context("130600113437")
        assert ctx["location_note"] == "الثلاجة الرئيسية"

    def test_get_center_context_unknown_device_returns_none(self, mapper):
        assert mapper.get_center_context("UNKNOWN_DEVICE") is None

    # ── استعلامات مباشرة ──────────────────────────────────────

    def test_get_equipment_id(self, mapper):
        eq_id = mapper.get_equipment_id("130600113437")
        assert eq_id == "EQ-FRIDGE-01"

    def test_get_equipment_id_unknown_returns_none(self, mapper):
        assert mapper.get_equipment_id("UNKNOWN") is None

    def test_get_center_id(self, mapper):
        center_id = mapper.get_center_id("130600113437")
        assert center_id == "TEST_CENTER_01"

    def test_get_center_id_unknown_returns_none(self, mapper):
        assert mapper.get_center_id("UNKNOWN") is None

    # ── EquipmentRecord ────────────────────────────────────────

    def test_get_equipment_record_from_registry(self, mapper):
        """جلب EquipmentRecord من equipment_registry."""
        eq = mapper.get_equipment_record("EQ-FRIDGE-01")
        assert eq is not None
        assert eq.equipment_id == "EQ-FRIDGE-01"
        assert eq.center_id == "TEST_CENTER_01"
        assert eq.equipment_type == EquipmentType.REFRIGERATOR
        assert eq.capacity_liters == 120.0

    def test_get_equipment_record_from_device_map_fallback(self, mapper):
        """جلب EquipmentRecord من device_map عند غياب equipment_registry."""
        eq = mapper.get_equipment_record("EQ-FRIDGE-02")
        assert eq is not None
        assert eq.equipment_id == "EQ-FRIDGE-02"
        assert eq.center_id == "CENTER_TRIPOLI_01"

    def test_get_equipment_record_unknown_returns_none(self, mapper):
        assert mapper.get_equipment_record("EQ-UNKNOWN") is None

    # ── استعلامات متعددة ──────────────────────────────────────

    def test_get_all_devices_for_equipment(self, mapper):
        """جلب جميع الأجهزة لمعدة معينة."""
        devices = mapper.get_all_devices_for_equipment("EQ-FRIDGE-01")
        assert "130600113437" in devices

    def test_get_all_equipment_for_center(self, mapper):
        """جلب جميع المعدات لمركز معين."""
        equipment = mapper.get_all_equipment_for_center("CENTER_TRIPOLI_01")
        assert "EQ-FRIDGE-02" in equipment
        assert "EQ-COLDROOM-01" in equipment
        # لا يجب أن تحتوي على معدات مركز آخر
        assert "EQ-FRIDGE-01" not in equipment

    def test_center_with_multiple_equipment(self, mapper):
        """مركز واحد يحتوي أكثر من معدة."""
        equipment = mapper.get_all_equipment_for_center("CENTER_TRIPOLI_01")
        assert len(equipment) == 2

    def test_is_mapped_true(self, mapper):
        assert mapper.is_mapped("130600113437") is True

    def test_is_mapped_false(self, mapper):
        assert mapper.is_mapped("NONEXISTENT") is False

    # ── التكامل مع الجهاز الحقيقي ─────────────────────────────

    def test_real_device_full_context(self, mapper):
        """
        الجهاز الحقيقي 130600113437 له سياق كامل.
        هذا الاختبار يتحقق من التكامل الكامل لـ A3.
        """
        ctx = mapper.get_center_context("130600113437")

        assert ctx["center_id"] == "TEST_CENTER_01"
        assert ctx["equipment_id"] == "EQ-FRIDGE-01"
        assert ctx["equipment_type"] == "REFRIGERATOR"
        assert ctx["status"] == "ACTIVE"

        eq = mapper.get_equipment_record("EQ-FRIDGE-01")
        assert eq is not None
        assert eq.center_id == "TEST_CENTER_01"
        assert eq.capacity_liters == 120.0