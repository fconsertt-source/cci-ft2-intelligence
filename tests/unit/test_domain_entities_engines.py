"""اختبارات تغطية لـ HeatExposure و DeviceReport و HeatExposureEngine"""

from datetime import datetime, timezone


from src.domain.engines.heat_exposure_engine import HeatExposureEngine
from src.domain.entities.device_report import DeviceReport
from src.domain.entities.heat_exposure import HeatExposure


class TestHeatExposure:
    def test_create_heat_exposure(self):
        he = HeatExposure(
            stage="WAREHOUSE",
            device_id="DEV-001",
            her=0.5,
            ccm=300.0,
            timestamp=datetime.now(timezone.utc),
        )
        assert he.stage == "WAREHOUSE"
        assert he.her == 0.5


class TestDeviceReport:
    def test_create_factory(self):
        report = DeviceReport.create(
            "DEV-001", status="generated", report_data={"key": "val"}
        )
        assert report.device_id == "DEV-001"
        assert report.status == "generated"
        assert report.generated_at is not None

    def test_to_dict(self):
        report = DeviceReport.create("DEV-001")
        d = report.to_dict()
        assert d["device_id"] == "DEV-001"
        assert "status" in d

    def test_default_status(self):
        report = DeviceReport.create("DEV-002")
        assert report.status == "generated"


class TestHeatExposureEngine:
    def setup_method(self):
        self.table = [(4.0, 1440), (8.0, 720), (12.0, 360), (25.0, 60)]
        self.engine = HeatExposureEngine(self.table)

    def test_compute_her_normal(self):
        her = self.engine.compute_her(8.0, 360)
        assert 0.0 < her <= 1.0

    def test_compute_her_capped_at_one(self):
        her = self.engine.compute_her(25.0, 9999)
        assert her == 1.0

    def test_compute_her_zero_duration(self):
        engine = HeatExposureEngine([])
        assert engine.compute_her(5.0, 60) == 0

    def test_below_min_temp(self):
        her = self.engine.compute_her(2.0, 100)
        assert her >= 0.0

    def test_above_max_temp(self):
        her = self.engine.compute_her(30.0, 100)
        assert her >= 0.0

    def test_interpolation_between_points(self):
        her = self.engine.compute_her(10.0, 200)
        assert 0.0 <= her <= 1.0
