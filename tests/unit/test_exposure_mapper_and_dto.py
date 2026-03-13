# tests/unit/test_exposure_mapper_and_dto.py
"""اختبارات تغطية لـ ExposureMapper و DeviceReportDTO"""
from datetime import datetime, timedelta, timezone

import pytest

from src.application.mappers.exposure_mapper import ExposureMapper
from src.domain.dtos.device_report_dto import DeviceReportDTO, ThermalExcursionDTO

# ---------------------------------------------------------------------------
# ExposureMapper
# ---------------------------------------------------------------------------


class TestExposureMapper:
    def _make_reading(self, value, timestamp):
        class R:
            pass

        r = R()
        r.value = value
        r.timestamp = timestamp
        return r

    def test_empty_readings_returns_empty(self):
        assert ExposureMapper.map_to_domain([]) == []

    def test_single_reading_returns_empty(self):
        r = self._make_reading(5.0, datetime(2024, 1, 1, 0, 0))
        assert ExposureMapper.map_to_domain([r]) == []

    def test_two_readings_returns_one_exposure(self):
        t1 = datetime(2024, 1, 1, 0, 0)
        t2 = datetime(2024, 1, 1, 0, 30)
        r1 = self._make_reading(5.0, t1)
        r2 = self._make_reading(6.0, t2)
        result = ExposureMapper.map_to_domain([r1, r2])
        assert len(result) == 1
        assert result[0].duration_minutes == 30.0
        assert result[0].temperature == 5.0

    def test_unsorted_readings_are_sorted(self):
        t1 = datetime(2024, 1, 1, 0, 0)
        t2 = datetime(2024, 1, 1, 1, 0)
        r1 = self._make_reading(5.0, t1)
        r2 = self._make_reading(7.0, t2)
        # أرسل بترتيب معكوس
        result = ExposureMapper.map_to_domain([r2, r1])
        assert len(result) == 1
        assert result[0].temperature == 5.0

    def test_dict_readings_fallback(self):
        t1 = datetime(2024, 1, 1, 0, 0)
        t2 = datetime(2024, 1, 1, 1, 0)
        r1 = {"value": 4.0, "timestamp": t1}
        r2 = {"value": 5.0, "timestamp": t2}
        result = ExposureMapper.map_to_domain([r1, r2])
        assert len(result) == 1
        assert result[0].duration_minutes == 60.0

    def test_zero_duration_excluded(self):
        t = datetime(2024, 1, 1, 0, 0)
        r1 = self._make_reading(5.0, t)
        r2 = self._make_reading(5.0, t)  # نفس الوقت
        result = ExposureMapper.map_to_domain([r1, r2])
        assert result == []

    def test_multiple_readings(self):
        base = datetime(2024, 1, 1, 0, 0)
        readings = [
            self._make_reading(4.0, base + timedelta(minutes=i * 10)) for i in range(5)
        ]
        result = ExposureMapper.map_to_domain(readings)
        assert len(result) == 4
        assert all(e.duration_minutes == 10.0 for e in result)


# ---------------------------------------------------------------------------
# DeviceReportDTO — الأسطر الناقصة
# ---------------------------------------------------------------------------


def make_dto(**kwargs):
    defaults = dict(
        device_id="DEV-001",
        vaccine_type="Pfizer",
        total_records=10,
        excursions=[],
        final_status="safe",
        scientific_rationale="test",
        generated_at=datetime.now(timezone.utc).isoformat(),
        ledger_hash="a" * 64,
    )
    defaults.update(kwargs)
    return DeviceReportDTO(**defaults)


class TestDeviceReportDTOValidation:
    def test_empty_device_id_raises(self):
        with pytest.raises(ValueError, match="device_id cannot be empty"):
            make_dto(device_id="   ")

    def test_invalid_ledger_hash_raises(self):
        with pytest.raises(ValueError, match="ledger_hash must be SHA-256"):
            make_dto(ledger_hash="short")

    def test_none_generated_at_gets_set(self):
        dto = make_dto(generated_at=None)
        assert dto.generated_at is not None

    def test_valid_dto_created(self):
        dto = make_dto()
        assert dto.device_id == "DEV-001"


class TestDeviceReportDTOGetBatchCounts:
    def _make_excursion(self, impact_level):
        return ThermalExcursionDTO(
            timestamp="2024-01-01T00:00:00",
            temperature=10.0,
            duration_minutes=60,
            impact_level=impact_level,
        )

    def test_empty_excursions(self):
        dto = make_dto()
        counts = dto.get_batch_counts()
        assert counts == {"safe": 0, "warning": 0, "discard": 0}

    def test_safe_excursion(self):
        dto = make_dto(excursions=[self._make_excursion("SAFE")])
        assert dto.get_batch_counts()["safe"] == 1

    def test_partial_excursion(self):
        dto = make_dto(excursions=[self._make_excursion("PARTIAL")])
        assert dto.get_batch_counts()["warning"] == 1

    def test_discard_excursion(self):
        dto = make_dto(excursions=[self._make_excursion("DISCARD")])
        assert dto.get_batch_counts()["discard"] == 1

    def test_mixed_excursions(self):
        excursions = [
            self._make_excursion("SAFE"),
            self._make_excursion("SAFE"),
            self._make_excursion("PARTIAL"),
            self._make_excursion("DISCARD"),
        ]
        dto = make_dto(excursions=excursions)
        counts = dto.get_batch_counts()
        assert counts == {"safe": 2, "warning": 1, "discard": 1}


class TestApplicationDeviceReportDTO:
    """تغطية src.application.dtos.device_report_dto"""

    def test_import_and_validate(self):
        from datetime import datetime, timezone

        from src.application.dtos.device_report_dto import (
            DeviceReportDTO,
        )

        dto = DeviceReportDTO(
            device_id="APP-001",
            vaccine_type="Pfizer",
            total_records=5,
            excursions=[],
            final_status="safe",
            scientific_rationale="test",
            generated_at=datetime.now(timezone.utc).isoformat(),
            ledger_hash="a" * 64,
        )
        assert dto.device_id == "APP-001"
        assert dto.get_batch_counts() == {"safe": 0, "warning": 0, "discard": 0}

    def test_empty_device_id_raises(self):
        from datetime import datetime, timezone

        import pytest

        from src.application.dtos.device_report_dto import DeviceReportDTO

        with pytest.raises(ValueError):
            DeviceReportDTO(
                device_id="",
                vaccine_type="Pfizer",
                total_records=5,
                excursions=[],
                final_status="safe",
                scientific_rationale="test",
                generated_at=datetime.now(timezone.utc).isoformat(),
                ledger_hash="a" * 64,
            )

    def test_none_generated_at(self):
        from src.application.dtos.device_report_dto import DeviceReportDTO

        dto = DeviceReportDTO(
            device_id="APP-001",
            vaccine_type="Pfizer",
            total_records=5,
            excursions=[],
            final_status="safe",
            scientific_rationale="test",
            generated_at=None,
            ledger_hash="a" * 64,
        )
        assert dto.generated_at is not None


class TestVaccineMapper:
    def test_to_vaccine_dto_basic(self):
        from src.application.mappers.vaccine_mapper import to_vaccine_dto

        class FakeVaccine:
            id = "VAC-001"
            category = "live"
            is_freeze_stable = True
            vvm_type = "VVM2"
            actions = {}
            full_loss_threshold_high = 37.0
            q10_value = 2.0
            ideal_temp = 5.0
            shelf_life_days = 365
            thaw_start_time = None
            thaw_duration_days = 70

        dto = to_vaccine_dto(FakeVaccine())
        assert dto.id == "VAC-001"
        assert dto.is_freeze_stable is True


class TestApplicationDTOExtraCoverage:
    def test_invalid_ledger_hash_raises(self):
        from datetime import datetime, timezone

        from src.application.dtos.device_report_dto import DeviceReportDTO

        with pytest.raises(ValueError, match="ledger_hash"):
            DeviceReportDTO(
                device_id="APP-001",
                vaccine_type="Pfizer",
                total_records=5,
                excursions=[],
                final_status="safe",
                scientific_rationale="test",
                generated_at=datetime.now(timezone.utc).isoformat(),
                ledger_hash="short",
            )

    def test_get_batch_counts_with_excursions(self):
        from datetime import datetime, timezone

        from src.application.dtos.device_report_dto import (
            DeviceReportDTO,
            ThermalExcursionDTO,
        )

        excursions = [
            ThermalExcursionDTO(
                timestamp="2024-01-01T00:00:00",
                temperature=10.0,
                duration_minutes=60,
                impact_level="SAFE",
            ),
            ThermalExcursionDTO(
                timestamp="2024-01-01T01:00:00",
                temperature=11.0,
                duration_minutes=30,
                impact_level="PARTIAL",
            ),
            ThermalExcursionDTO(
                timestamp="2024-01-01T02:00:00",
                temperature=12.0,
                duration_minutes=20,
                impact_level="DISCARD",
            ),
        ]
        dto = DeviceReportDTO(
            device_id="APP-001",
            vaccine_type="Pfizer",
            total_records=5,
            excursions=excursions,
            final_status="safe",
            scientific_rationale="test",
            generated_at=datetime.now(timezone.utc).isoformat(),
            ledger_hash="a" * 64,
        )
        counts = dto.get_batch_counts()
        assert counts == {"safe": 1, "warning": 1, "discard": 1}


class TestApplicationDTOExtraCoverage:
    def test_invalid_ledger_hash_raises(self):
        from datetime import datetime, timezone

        from src.application.dtos.device_report_dto import DeviceReportDTO

        with pytest.raises(ValueError, match="ledger_hash"):
            DeviceReportDTO(
                device_id="APP-001",
                vaccine_type="Pfizer",
                total_records=5,
                excursions=[],
                final_status="safe",
                scientific_rationale="test",
                generated_at=datetime.now(timezone.utc).isoformat(),
                ledger_hash="short",
            )

    def test_get_batch_counts_with_excursions(self):
        from datetime import datetime, timezone

        from src.application.dtos.device_report_dto import (
            DeviceReportDTO,
            ThermalExcursionDTO,
        )

        excursions = [
            ThermalExcursionDTO(
                timestamp="2024-01-01T00:00:00",
                temperature=10.0,
                duration_minutes=60,
                impact_level="SAFE",
            ),
            ThermalExcursionDTO(
                timestamp="2024-01-01T01:00:00",
                temperature=11.0,
                duration_minutes=30,
                impact_level="PARTIAL",
            ),
            ThermalExcursionDTO(
                timestamp="2024-01-01T02:00:00",
                temperature=12.0,
                duration_minutes=20,
                impact_level="DISCARD",
            ),
        ]
        dto = DeviceReportDTO(
            device_id="APP-001",
            vaccine_type="Pfizer",
            total_records=5,
            excursions=excursions,
            final_status="safe",
            scientific_rationale="test",
            generated_at=datetime.now(timezone.utc).isoformat(),
            ledger_hash="a" * 64,
        )
        counts = dto.get_batch_counts()
        assert counts == {"safe": 1, "warning": 1, "discard": 1}


class TestAbstractPortsNotImplemented:

    def test_i_reporter_generate_raises(self):
        import pytest

        from src.application.ports.i_reporter import IReporter

        class ConcreteReporter(IReporter):
            def generate(self, result):
                return super().generate(result)

        reporter = ConcreteReporter()
        with pytest.raises(NotImplementedError):
            reporter.generate(None)

    def test_thermal_impact_calculator_raises(self):
        import pytest

        from src.application.ports.thermal_impact_calculator_port import (
            ThermalImpactCalculatorPort,
        )

        class ConcreteCalc(ThermalImpactCalculatorPort):
            def evaluate(self, temperature, duration_minutes, specification):
                return super().evaluate(temperature, duration_minutes, specification)

        calc = ConcreteCalc()
        with pytest.raises(NotImplementedError):
            calc.evaluate(5.0, 60, None)


class TestRemainingPortsNotImplemented:

    def test_vaccine_specification_port_raises(self):
        from src.application.ports.vaccine_specification_port import (
            VaccineSpecificationPort,
        )

        class C(VaccineSpecificationPort):
            def get_spec(self, vaccine_type):
                return super().get_spec(vaccine_type)

        with pytest.raises(NotImplementedError):
            C().get_spec("Pfizer")

    def test_validation_protocol_port_raises(self):
        from src.application.ports.validation_protocol_port import (
            ValidationProtocolPort,
        )

        class C(ValidationProtocolPort):
            def get_protocol(self, vaccine_type):
                return super().get_protocol(vaccine_type)

        with pytest.raises(NotImplementedError):
            C().get_protocol("Pfizer")


class TestFixedPortsNotImplemented:
    def test_device_repository_raises(self):
        from src.application.ports.device_repository_port import DeviceRepositoryPort

        class C(DeviceRepositoryPort):
            def get_device_history(self, device_id, date_from=None, date_to=None):
                return super().get_device_history(device_id)

            def get_all_device_ids(self, date_from=None, date_to=None):
                return super().get_all_device_ids()

        with pytest.raises(NotImplementedError):
            C().get_device_history("X")
        with pytest.raises(NotImplementedError):
            C().get_all_device_ids()

    def test_vaccine_specification_raises(self):
        from src.application.ports.vaccine_specification_port import (
            VaccineSpecificationPort,
        )

        class C(VaccineSpecificationPort):
            def get_spec(self, vaccine_type):
                return super().get_spec(vaccine_type)

        with pytest.raises(NotImplementedError):
            C().get_spec("Pfizer")
