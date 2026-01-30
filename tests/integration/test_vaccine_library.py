import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from src.application.use_cases.evaluate_cold_chain_safety_uc import EvaluateColdChainSafetyUC
from src.application.dtos.analysis_result_dto import VaccineStatus
from src.core.entities.temperature_reading import TemperatureReading
from src.core.entities.vaccine import Vaccine
from src.core.enums.vvm_stage import VVMStage

@pytest.fixture
def mock_reader():
    return MagicMock()

@pytest.fixture
def mock_repo():
    return MagicMock()

class TestVaccineLibraryIntegration:
    """
    Tests the new v1.1.0 features: Adaptive Rules and Ultra-Cold Tracking.
    """

    def test_freeze_stable_vaccine_not_rejected(self, mock_reader, mock_repo):
        # Setup: OPV is freeze-stable (id: opv in library)
        vaccine = Vaccine(
            id="opv", name="Oral Polio", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=30, reference_table=[],
            q10_value=2.0, ideal_temp=5.0
        )
        mock_reader.get_vaccines.return_value = [vaccine]

        # Readings: Explicit freeze (-5°C)
        t0 = datetime.now()
        readings = [
            TemperatureReading("opv", -5.0, t0),
            TemperatureReading("opv", -5.0, t0 + timedelta(hours=1)),
            TemperatureReading("opv", 5.0, t0 + timedelta(hours=2)),
        ]
        mock_reader.read_all.return_value = readings

        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()

        # Should be SAFE because it's freeze-stable
        assert results[0].status == VaccineStatus.SAFE
        assert any("مقاوم للتجميد" in r["reason"] for r in results[0].audit_log)

    def test_freeze_sensitive_vaccine_rejected(self, mock_reader, mock_repo):
        # Setup: HepB is freeze-sensitive (id: hepatitis_b in library)
        vaccine = Vaccine(
            id="hepatitis_b", name="HepB", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=30, reference_table=[]
        )
        mock_reader.get_vaccines.return_value = [vaccine]

        # Readings: Freeze
        t0 = datetime.now()
        readings = [
            TemperatureReading("hepatitis_b", -2.0, t0),
            TemperatureReading("hepatitis_b", 5.0, t0 + timedelta(hours=1)),
        ]
        mock_reader.read_all.return_value = readings

        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()

        # Should be DISCARD
        assert results[0].status == VaccineStatus.DISCARD
        assert any("انتهاك تجميد" in r["reason"] for r in results[0].audit_log)
        assert any("اختبار الرج" in r["reason"] for r in results[0].audit_log)

    def test_ultra_cold_thaw_timeout(self, mock_reader, mock_repo):
        # Setup: Pfizer (id: pfizer_comirnaty in library)
        # It has 70 days fridge life after thawing.
        # We'll set thaw_start_time to 75 days ago.
        thaw_date = datetime.now() - timedelta(days=75)
        vaccine = Vaccine(
            id="pfizer_comirnaty", name="Pfizer", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=300, reference_table=[],
            thaw_start_time=thaw_date
        )
        mock_reader.get_vaccines.return_value = [vaccine]

        # Basic safe readings
        t0 = datetime.now()
        readings = [TemperatureReading("pfizer_comirnaty", 5.0, t0)]
        mock_reader.read_all.return_value = readings

        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()

        # Should be DISCARD due to thaw timeout
        assert results[0].status == VaccineStatus.DISCARD
        assert any("انقضاء صلاحية الثوب" in r["reason"] for r in results[0].audit_log)

    def test_ultra_cold_thaw_countdown(self, mock_reader, mock_repo):
        # Thaw started 10 days ago (Limit 70)
        thaw_date = datetime.now() - timedelta(days=10)
        vaccine = Vaccine(
            id="pfizer_comirnaty", name="Pfizer", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=300, reference_table=[],
            thaw_start_time=thaw_date
        )
        mock_reader.get_vaccines.return_value = [vaccine]

        readings = [TemperatureReading("pfizer_comirnaty", 5.0, datetime.now())]
        mock_reader.read_all.return_value = readings

        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()

        # Should be SAFE with a countdown warning
        assert results[0].status == VaccineStatus.SAFE
        assert any("متبقي 60 يوم" in r["reason"] for r in results[0].audit_log)
        assert results[0].alert_level == "YELLOW"
        assert results[0].thaw_remaining_hours == pytest.approx(60 * 24, abs=1)

    def test_stability_budget_alert_levels(self, mock_reader, mock_repo):
        # Setup: Custom vaccine not in library to avoid strict 8C limit
        # HER calculation: 
        # Shelf life = 48 hours. 
        # 18 hours at 15°C (Factor 2) -> Deg = 36h. 
        # HER = 36/48 = 0.75.
        vaccine = Vaccine(
            id="test_yellow_vaccine", name="YellowTest", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=2, reference_table=[],
            q10_value=2.0, ideal_temp=5.0
        )
        mock_reader.get_vaccines.return_value = [vaccine]

        t0 = datetime.now() - timedelta(hours=20)
        readings = [
            TemperatureReading("test_yellow_vaccine", 15.0, t0),
            TemperatureReading("test_yellow_vaccine", 15.0, t0 + timedelta(hours=18)),
            TemperatureReading("test_yellow_vaccine", 5.0, t0 + timedelta(hours=20)),
        ]
        mock_reader.read_all.return_value = readings

        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()

        # HER=0.833, Status=PARTIAL, Alert=YELLOW
        assert results[0].alert_level == "YELLOW"
        assert results[0].stability_budget_consumed_pct == pytest.approx(83.33, abs=0.1)
        assert any("تنبيه أصفر" in r["reason"] for r in results[0].audit_log)
