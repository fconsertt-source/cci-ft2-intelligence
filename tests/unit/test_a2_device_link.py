# tests/unit/test_a2_device_link.py
"""
اختبارات A2 — DeviceStatus + DeviceLink + DeviceRegistry

تغطية:
  1. DeviceLink — إنشاء، حساب الفجوة، الحكم على السلسلة
  2. DeviceRegistry — تسجيل، استبدال، تقاعد، استعلامات
  3. سيناريوهات واقعية — فجوة مقبولة، فجوة طويلة، سلسلة متعددة
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.entities.device_link import DeviceLink
from src.domain.enums.device_status import DeviceStatus
from src.domain.services.device_registry import DeviceRegistry


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def registry(tmp_path):
    """DeviceRegistry مؤقت لكل اختبار."""
    return DeviceRegistry(registry_dir=tmp_path / "registry")


def dt(year=2024, month=7, day=1, hour=0, minute=0) -> datetime:
    """اختصار لإنشاء datetime بـ UTC."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# ══════════════════════════════════════════════════════════════
# 1. اختبارات DeviceStatus
# ══════════════════════════════════════════════════════════════

class TestDeviceStatus:

    def test_status_values(self):
        assert DeviceStatus.ACTIVE.value == "ACTIVE"
        assert DeviceStatus.RETIRED.value == "RETIRED"
        assert DeviceStatus.REPLACED.value == "REPLACED"

    def test_status_from_string(self):
        assert DeviceStatus("ACTIVE") == DeviceStatus.ACTIVE
        assert DeviceStatus("RETIRED") == DeviceStatus.RETIRED


# ══════════════════════════════════════════════════════════════
# 2. اختبارات DeviceLink
# ══════════════════════════════════════════════════════════════

class TestDeviceLink:

    def test_create_link_no_gap(self):
        """استبدال فوري — لا فجوة زمنية."""
        last = dt(hour=10, minute=0)
        first = dt(hour=10, minute=5)

        link = DeviceLink.create(
            old_device_id="DEV-OLD",
            new_device_id="DEV-NEW",
            equipment_id="EQ-001",
            handover_date=dt(hour=10, minute=0),
            old_device_last_reading=last,
            new_device_first_reading=first,
        )

        assert link.gap_hours == pytest.approx(5 / 60, abs=1e-4)
        assert link.cold_chain_intact is True

    def test_gap_exactly_2_hours_intact(self):
        """فجوة بالضبط ساعتان → السلسلة متصلة."""
        last = dt(hour=8, minute=0)
        first = dt(hour=10, minute=0)

        link = DeviceLink.create(
            old_device_id="DEV-OLD",
            new_device_id="DEV-NEW",
            equipment_id="EQ-001",
            handover_date=dt(hour=9),
            old_device_last_reading=last,
            new_device_first_reading=first,
        )

        assert link.gap_hours == pytest.approx(2.0, abs=1e-4)
        assert link.cold_chain_intact is True

    def test_gap_over_2_hours_broken(self):
        """فجوة 5 ساعات → السلسلة منقطعة."""
        last = dt(hour=8, minute=0)
        first = dt(hour=13, minute=0)

        link = DeviceLink.create(
            old_device_id="DEV-OLD",
            new_device_id="DEV-NEW",
            equipment_id="EQ-001",
            handover_date=dt(hour=9),
            old_device_last_reading=last,
            new_device_first_reading=first,
        )

        assert link.gap_hours == pytest.approx(5.0, abs=1e-4)
        assert link.cold_chain_intact is False

    def test_no_readings_gap_is_zero(self):
        """بدون قراءات حدية → الفجوة صفر والسلسلة متصلة."""
        link = DeviceLink.create(
            old_device_id="DEV-OLD",
            new_device_id="DEV-NEW",
            equipment_id="EQ-001",
            handover_date=dt(),
        )

        assert link.gap_hours == 0.0
        assert link.cold_chain_intact is True

    def test_same_device_id_raises(self):
        """نفس معرف الجهاز القديم والجديد → خطأ."""
        with pytest.raises(ValueError, match="must be different"):
            DeviceLink.create(
                old_device_id="DEV-001",
                new_device_id="DEV-001",
                equipment_id="EQ-001",
                handover_date=dt(),
            )

    def test_empty_device_id_raises(self):
        with pytest.raises(ValueError):
            DeviceLink.create(
                old_device_id="",
                new_device_id="DEV-NEW",
                equipment_id="EQ-001",
                handover_date=dt(),
            )

    def test_empty_equipment_id_raises(self):
        with pytest.raises(ValueError):
            DeviceLink.create(
                old_device_id="DEV-OLD",
                new_device_id="DEV-NEW",
                equipment_id="",
                handover_date=dt(),
            )

    def test_serialization_roundtrip(self):
        """to_dict → from_dict → نفس القيم."""
        last = dt(hour=10)
        first = dt(hour=11)

        original = DeviceLink.create(
            old_device_id="DEV-OLD",
            new_device_id="DEV-NEW",
            equipment_id="EQ-001",
            handover_date=dt(hour=10, minute=30),
            old_device_last_reading=last,
            new_device_first_reading=first,
            gap_reason="صيانة دورية",
            created_by="admin",
        )

        restored = DeviceLink.from_dict(original.to_dict())

        assert restored.old_device_id == original.old_device_id
        assert restored.new_device_id == original.new_device_id
        assert restored.equipment_id == original.equipment_id
        assert restored.gap_hours == original.gap_hours
        assert restored.cold_chain_intact == original.cold_chain_intact
        assert restored.gap_reason == original.gap_reason

    def test_str_representation(self):
        link = DeviceLink.create(
            old_device_id="DEV-OLD",
            new_device_id="DEV-NEW",
            equipment_id="EQ-001",
            handover_date=dt(),
        )
        text = str(link)
        assert "DEV-OLD" in text
        assert "DEV-NEW" in text
        assert "EQ-001" in text


# ══════════════════════════════════════════════════════════════
# 3. اختبارات DeviceRegistry
# ══════════════════════════════════════════════════════════════

class TestDeviceRegistry:

    def test_register_new_device(self, registry):
        record = registry.register_device(
            device_id="DEV-001",
            serial_number="130600113437",
            equipment_id="EQ-FRIDGE-01",
        )
        assert record.device_id == "DEV-001"
        assert record.status == DeviceStatus.ACTIVE
        assert record.equipment_id == "EQ-FRIDGE-01"

    def test_register_duplicate_raises(self, registry):
        registry.register_device("DEV-001", "SN-001", "EQ-01")
        with pytest.raises(ValueError, match="مسجل مسبقاً"):
            registry.register_device("DEV-001", "SN-002", "EQ-01")

    def test_get_device(self, registry):
        registry.register_device("DEV-001", "SN-001", "EQ-01")
        record = registry.get_device("DEV-001")
        assert record is not None
        assert record.device_id == "DEV-001"

    def test_get_nonexistent_device_returns_none(self, registry):
        assert registry.get_device("NONEXISTENT") is None

    def test_replace_device_updates_statuses(self, registry):
        """الاستبدال يغير القديم إلى REPLACED ويضيف الجديد كـ ACTIVE."""
        registry.register_device("DEV-OLD", "SN-OLD", "EQ-01")

        link = registry.replace_device(
            old_device_id="DEV-OLD",
            new_device_id="DEV-NEW",
            new_serial_number="SN-NEW",
            handover_date=dt(),
        )

        old = registry.get_device("DEV-OLD")
        new = registry.get_device("DEV-NEW")

        if old.status != DeviceStatus.REPLACED:
            raise AssertionError(f"Expected REPLACED, got {old.status}")
        if old.replaced_by != "DEV-NEW":
            raise AssertionError(f"Expected replaced_by DEV-NEW, got {old.replaced_by}")
        if new.status != DeviceStatus.ACTIVE:
            raise AssertionError(f"Expected ACTIVE, got {new.status}")
        if new.equipment_id != "EQ-01":
            raise AssertionError(f"Expected equipment_id EQ-01, got {new.equipment_id}")
        assert isinstance(link, DeviceLink)

    def test_replace_nonactive_device_raises(self, registry):
        """لا يمكن استبدال جهاز غير نشط."""
        registry.register_device("DEV-OLD", "SN-OLD", "EQ-01")
        registry.retire_device("DEV-OLD")

        with pytest.raises(ValueError, match="غير نشط"):
            registry.replace_device(
                old_device_id="DEV-OLD",
                new_device_id="DEV-NEW",
                new_serial_number="SN-NEW",
                handover_date=dt(),
            )

    def test_retire_device(self, registry):
        registry.register_device("DEV-001", "SN-001", "EQ-01")
        record = registry.retire_device("DEV-001", reason="انتهت الصلاحية")
        assert record.status == DeviceStatus.RETIRED
        assert record.retired_at is not None

    def test_retire_nonactive_raises(self, registry):
        registry.register_device("DEV-001", "SN-001", "EQ-01")
        registry.retire_device("DEV-001")
        with pytest.raises(ValueError, match="ليس نشطاً"):
            registry.retire_device("DEV-001")

    def test_get_active_device_for_equipment(self, registry):
        registry.register_device("DEV-OLD", "SN-OLD", "EQ-01")
        registry.replace_device(
            old_device_id="DEV-OLD",
            new_device_id="DEV-NEW",
            new_serial_number="SN-NEW",
            handover_date=dt(),
        )

        active = registry.get_active_device_for_equipment("EQ-01")
        assert active is not None
        assert active.device_id == "DEV-NEW"

    def test_get_device_chain_ordered(self, registry):
        """السلسلة مرتبة من الأقدم للأحدث."""
        registry.register_device("DEV-1", "SN-1", "EQ-01")
        registry.replace_device(
            "DEV-1", "DEV-2", "SN-2", dt(month=2)
        )
        registry.replace_device(
            "DEV-2", "DEV-3", "SN-3", dt(month=3)
        )

        chain = registry.get_device_chain("EQ-01")
        ids = [r.device_id for r in chain]
        assert ids == ["DEV-1", "DEV-2", "DEV-3"]

    def test_cold_chain_intact_no_gaps(self, registry):
        """استبدالات فورية → السلسلة متصلة."""
        registry.register_device("DEV-1", "SN-1", "EQ-01")
        registry.replace_device(
            "DEV-1", "DEV-2", "SN-2", dt(hour=10),
            old_device_last_reading=dt(hour=10),
            new_device_first_reading=dt(hour=10, minute=30),
        )

        assert registry.is_cold_chain_intact("EQ-01") is True

    def test_cold_chain_broken_with_gap(self, registry):
        """فجوة 6 ساعات → السلسلة منقطعة."""
        registry.register_device("DEV-1", "SN-1", "EQ-01")
        registry.replace_device(
            "DEV-1", "DEV-2", "SN-2", dt(hour=12),
            old_device_last_reading=dt(hour=6),
            new_device_first_reading=dt(hour=12),
        )

        assert registry.is_cold_chain_intact("EQ-01") is False

    def test_get_all_device_ids_for_equipment(self, registry):
        """جلب جميع معرفات الأجهزة لاستخدامها في استعلام ft2_data."""
        registry.register_device("DEV-1", "SN-1", "EQ-01")
        registry.replace_device("DEV-1", "DEV-2", "SN-2", dt(month=2))
        registry.replace_device("DEV-2", "DEV-3", "SN-3", dt(month=3))

        ids = registry.get_all_device_ids_for_equipment("EQ-01")
        assert set(ids) == {"DEV-1", "DEV-2", "DEV-3"}

    def test_persistence_across_instances(self, tmp_path):
        """البيانات تُحفظ وتُحمَّل بين إنشاءات مختلفة للـ Registry."""
        reg_dir = tmp_path / "registry"

        # Instance 1: تسجيل واستبدال
        reg1 = DeviceRegistry(registry_dir=reg_dir)
        reg1.register_device("DEV-OLD", "SN-OLD", "EQ-01")
        reg1.replace_device(
            "DEV-OLD", "DEV-NEW", "SN-NEW", dt()
        )

        # Instance 2: تحميل من نفس المجلد
        reg2 = DeviceRegistry(registry_dir=reg_dir)

        old = reg2.get_device("DEV-OLD")
        new = reg2.get_device("DEV-NEW")
        links = reg2.get_links_for_equipment("EQ-01")

        assert old.status == DeviceStatus.REPLACED
        assert new.status == DeviceStatus.ACTIVE
        assert len(links) == 1

    def test_empty_equipment_returns_no_active(self, registry):
        """معدة غير مسجلة → لا جهاز نشط."""
        active = registry.get_active_device_for_equipment("EQ-UNKNOWN")
        assert active is None