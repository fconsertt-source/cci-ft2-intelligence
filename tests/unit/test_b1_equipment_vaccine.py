# tests/unit/test_b1_equipment_vaccine.py
"""
اختبارات B1 — EquipmentVaccine + EquipmentVaccineRepository

تغطية:
  1. EquipmentVaccine — إنشاء، تحقق، VVM، انتهاء الصلاحية
  2. VVMStageValue — المراحل الأربع
  3. EquipmentVaccineRepository — CRUD + تحميل JSON
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from src.domain.entities.equipment_vaccine import (
    EquipmentVaccine,
    VVMStageValue,
)
from src.infrastructure.adapters.equipment_vaccine_repository import (
    EquipmentVaccineRepository,
)


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════

def future_date(days: int = 365) -> date:
    return date.today() + timedelta(days=days)


def past_date(days: int = 10) -> date:
    return date.today() - timedelta(days=days)


def make_vaccine(
    equipment_id: str = "EQ-001",
    vaccine_type: str = "HEPB",
    batch: str = "B-001",
    expiry: date = None,
    has_vvm: bool = False,
    vvm_stage: int = None,
) -> EquipmentVaccine:
    return EquipmentVaccine(
        equipment_id=equipment_id,
        center_id="CTR-001",
        vaccine_type=vaccine_type,
        batch_number=batch,
        expiry_date=expiry or future_date(),
        has_vvm=has_vvm,
        vvm_stage=VVMStageValue(vvm_stage) if vvm_stage else None,
    )


@pytest.fixture
def repo(tmp_path) -> EquipmentVaccineRepository:
    return EquipmentVaccineRepository(data_path=tmp_path / "equipment_vaccines.json")


# ══════════════════════════════════════════════════════════════
# 1. اختبارات VVMStageValue
# ══════════════════════════════════════════════════════════════

class TestVVMStageValue:

    def test_stage_1_usable(self):
        assert VVMStageValue.STAGE_1.is_usable is True

    def test_stage_2_usable(self):
        assert VVMStageValue.STAGE_2.is_usable is True

    def test_stage_3_not_usable(self):
        assert VVMStageValue.STAGE_3.is_usable is False

    def test_stage_4_not_usable(self):
        assert VVMStageValue.STAGE_4.is_usable is False

    def test_stage_labels_arabic(self):
        for stage in VVMStageValue:
            assert len(stage.label_ar) > 0

    def test_from_int(self):
        assert VVMStageValue(1) == VVMStageValue.STAGE_1
        assert VVMStageValue(4) == VVMStageValue.STAGE_4


# ══════════════════════════════════════════════════════════════
# 2. اختبارات EquipmentVaccine
# ══════════════════════════════════════════════════════════════

class TestEquipmentVaccine:

    def test_create_without_vvm(self):
        v = make_vaccine(has_vvm=False)
        assert v.has_vvm is False
        assert v.vvm_stage is None
        assert v.vvm_usable is True  # لا VVM → نفترض صالح

    def test_create_with_vvm_stage_1(self):
        v = make_vaccine(has_vvm=True, vvm_stage=1)
        assert v.has_vvm is True
        assert v.vvm_stage == VVMStageValue.STAGE_1
        assert v.vvm_usable is True

    def test_create_with_vvm_stage_3_not_usable(self):
        v = make_vaccine(has_vvm=True, vvm_stage=3)
        assert v.vvm_usable is False

    def test_has_vvm_true_requires_stage(self):
        """has_vvm=True بدون vvm_stage → خطأ."""
        with pytest.raises(ValueError, match="vvm_stage مطلوب"):
            EquipmentVaccine(
                equipment_id="EQ-001",
                center_id="CTR-001",
                vaccine_type="HEPB",
                batch_number="B-001",
                expiry_date=future_date(),
                has_vvm=True,
                vvm_stage=None,
            )

    def test_has_vvm_false_with_stage_raises(self):
        """has_vvm=False مع vvm_stage → خطأ."""
        with pytest.raises(ValueError, match="vvm_stage يجب أن يكون None"):
            EquipmentVaccine(
                equipment_id="EQ-001",
                center_id="CTR-001",
                vaccine_type="HEPB",
                batch_number="B-001",
                expiry_date=future_date(),
                has_vvm=False,
                vvm_stage=VVMStageValue.STAGE_1,
            )

    def test_empty_equipment_id_raises(self):
        with pytest.raises(ValueError, match="equipment_id"):
            make_vaccine(equipment_id="")

    def test_empty_vaccine_type_raises(self):
        with pytest.raises(ValueError, match="vaccine_type"):
            make_vaccine(vaccine_type="")

    def test_is_expired_false(self):
        v = make_vaccine(expiry=future_date(100))
        assert v.is_expired is False

    def test_is_expired_true(self):
        v = make_vaccine(expiry=past_date(5))
        assert v.is_expired is True

    def test_days_to_expiry_positive(self):
        v = make_vaccine(expiry=future_date(30))
        assert v.days_to_expiry > 0

    def test_days_to_expiry_negative_when_expired(self):
        v = make_vaccine(expiry=past_date(10))
        assert v.days_to_expiry < 0

    def test_immutable(self):
        v = make_vaccine()
        with pytest.raises((AttributeError, TypeError)):
            v.vaccine_type = "OPV"

    def test_serialization_roundtrip_without_vvm(self):
        original = make_vaccine(has_vvm=False)
        restored = EquipmentVaccine.from_dict(original.to_dict())
        assert restored.vaccine_type == original.vaccine_type
        assert restored.batch_number == original.batch_number
        assert restored.expiry_date == original.expiry_date
        assert restored.has_vvm == original.has_vvm
        assert restored.vvm_stage is None

    def test_serialization_roundtrip_with_vvm(self):
        original = make_vaccine(has_vvm=True, vvm_stage=2)
        restored = EquipmentVaccine.from_dict(original.to_dict())
        assert restored.vvm_stage == VVMStageValue.STAGE_2
        assert restored.has_vvm is True

    def test_entry_id_auto_generated(self):
        v1 = make_vaccine()
        v2 = make_vaccine()
        assert v1.entry_id != v2.entry_id


# ══════════════════════════════════════════════════════════════
# 3. اختبارات EquipmentVaccineRepository
# ══════════════════════════════════════════════════════════════

class TestEquipmentVaccineRepository:

    def test_empty_on_init(self, repo):
        assert repo.get_by_equipment("EQ-001") == []

    def test_add_and_retrieve(self, repo):
        v = make_vaccine(equipment_id="EQ-001")
        repo.add(v)
        result = repo.get_by_equipment("EQ-001")
        assert len(result) == 1
        assert result[0].vaccine_type == "HEPB"

    def test_get_by_center(self, repo):
        v = make_vaccine(equipment_id="EQ-001")
        repo.add(v)
        result = repo.get_by_center("CTR-001")
        assert len(result) == 1

    def test_get_by_entry_id(self, repo):
        v = make_vaccine()
        repo.add(v)
        found = repo.get_by_entry_id(v.entry_id)
        assert found is not None
        assert found.entry_id == v.entry_id

    def test_get_by_entry_id_not_found(self, repo):
        assert repo.get_by_entry_id("NONEXISTENT") is None

    def test_remove_vaccine(self, repo):
        v = make_vaccine()
        repo.add(v)
        result = repo.remove(v.entry_id)
        assert result is True
        assert repo.get_by_entry_id(v.entry_id) is None

    def test_remove_nonexistent_returns_false(self, repo):
        assert repo.remove("NONEXISTENT") is False

    def test_get_expired(self, repo):
        active = make_vaccine(expiry=future_date(100))
        expired = make_vaccine(expiry=past_date(5), batch="EXPIRED")
        repo.add(active)
        repo.add(expired)
        result = repo.get_expired()
        assert len(result) == 1
        assert result[0].batch_number == "EXPIRED"

    def test_get_active_excludes_expired(self, repo):
        active = make_vaccine(equipment_id="EQ-001", expiry=future_date(100))
        expired = make_vaccine(equipment_id="EQ-001", expiry=past_date(5), batch="EXP")
        repo.add(active)
        repo.add(expired)
        result = repo.get_active("EQ-001")
        assert len(result) == 1
        assert result[0].expiry_date == active.expiry_date

    def test_update_vvm_stage(self, repo):
        v = make_vaccine(has_vvm=True, vvm_stage=1)
        repo.add(v)
        updated = repo.update_vvm_stage(v.entry_id, 2)
        assert updated is not None
        assert updated.vvm_stage == VVMStageValue.STAGE_2

    def test_persistence_across_instances(self, tmp_path):
        """البيانات تُحفظ وتُحمَّل بين إنشاءات مختلفة."""
        path = tmp_path / "eq_vaccines.json"
        repo1 = EquipmentVaccineRepository(data_path=path)
        v = make_vaccine(equipment_id="EQ-001", vaccine_type="OPV")
        repo1.add(v)

        repo2 = EquipmentVaccineRepository(data_path=path)
        result = repo2.get_by_equipment("EQ-001")
        assert len(result) == 1
        assert result[0].vaccine_type == "OPV"

    def test_load_from_real_json_format(self, tmp_path):
        """تحميل من تنسيق JSON الحقيقي."""
        data = {
            "equipment_vaccines": [
                {
                    "equipment_id": "EQ-FRIDGE-01",
                    "center_id": "TEST_CENTER_01",
                    "vaccines": [
                        {
                            "entry_id": "VE-001",
                            "vaccine_type": "HEPB",
                            "batch_number": "B-2024-001",
                            "expiry_date": "2026-01-01",
                            "has_vvm": True,
                            "vvm_stage": 1,
                        }
                    ],
                }
            ]
        }
        path = tmp_path / "eq_vaccines.json"
        with open(path, "w") as f:
            json.dump(data, f)

        repo = EquipmentVaccineRepository(data_path=path)
        result = repo.get_by_equipment("EQ-FRIDGE-01")
        assert len(result) == 1
        assert result[0].vaccine_type == "HEPB"
        assert result[0].vvm_stage == VVMStageValue.STAGE_1
        assert result[0].center_id == "TEST_CENTER_01"