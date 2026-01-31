import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from src.application.use_cases.evaluate_cold_chain_safety_uc import EvaluateColdChainSafetyUC
from src.application.dtos.analysis_result_dto import VaccineStatus
from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.entities.vaccine import Vaccine

@pytest.fixture
def mock_reader():
    """Provides a mock for the data reader."""
    return MagicMock()

@pytest.fixture
def mock_repo():
    """Provides a mock for the data repository."""
    return MagicMock()

class TestEvaluateColdChainSafetyUCWithQ10:
    
    def test_execute_q10_safe_scenario(self, mock_reader, mock_repo):
        """
        Tests a scenario where the vaccine is exposed to some heat but remains
        well within its Q10-calculated shelf life.
        """
        # Setup: A vaccine with a 30-day shelf life.
        vaccine = Vaccine(
            id="v1", name="Polio", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=30, reference_table=[],
            q10_value=2.0, ideal_temp=5.0
        )
        mock_reader.get_vaccines.return_value = [vaccine]
        
        # Setup: Readings showing 12 hours at 15°C.
        # Degradation hours = 12 * (2 ^ ((15-5)/10)) = 12 * 2 = 24 hours.
        # Shelf life = 30 * 24 = 720 hours.
        # HER = 24 / 720 ~= 0.033. This is SAFE.
        t0 = datetime.now()
        readings = [
            TemperatureReading("v1", 15.0, t0),
            TemperatureReading("v1", 5.0, t0 + timedelta(hours=12)),
        ]
        mock_reader.read_all.return_value = readings
        
        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()
        
        assert len(results) == 1
        result = results[0]
        assert result.vaccine_id == "v1"
        assert result.status == VaccineStatus.SAFE
        assert result.her == pytest.approx(24.0 / (30 * 24))
        mock_repo.save_all.assert_called_once()

    def test_execute_q10_discard_scenario(self, mock_reader, mock_repo):
        """
        Tests a scenario where the cumulative heat exposure according to the
        Q10 model exceeds the vaccine's shelf life, leading to a DISCARD status.
        """
        # Setup: A vaccine with a short 3-day shelf life (72 hours).
        vaccine = Vaccine(
            id="v2", name="SensitiveVax", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=3, reference_table=[],
            q10_value=2.0, ideal_temp=5.0
        )
        mock_reader.get_vaccines.return_value = [vaccine]
        
        # Setup: Readings showing significant heat exposure.
        # Segment 1: 24 hours starting at 15°C. Degradation = 24 * (2^1) = 48 hours.
        # Segment 2: 12 hours starting at 25°C. Degradation = 12 * (2^2) = 48 hours.
        # Total degradation = 48 + 48 = 96 hours.
        # Shelf life = 3 * 24 = 72 hours.
        # HER = 96 / 72 = 1.333. This is DISCARD.
        t0 = datetime.now()
        readings = [
            TemperatureReading("v2", 15.0, t0),
            TemperatureReading("v2", 25.0, t0 + timedelta(hours=24)),
            TemperatureReading("v2", 5.0, t0 + timedelta(hours=36)),
        ]
        mock_reader.read_all.return_value = readings
        
        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()
        
        assert len(results) == 1
        result = results[0]
        assert result.vaccine_id == "v2"
        assert result.status == VaccineStatus.DISCARD
        assert result.her == pytest.approx(96.0 / 72.0)

    def test_execute_q10_partial_scenario(self, mock_reader, mock_repo):
        """
        Tests a scenario where heat exposure is significant (>50% of shelf life)
        but not enough to discard, leading to PARTIAL status.
        """
        # Setup: 10-day shelf life (240 hours).
        vaccine = Vaccine(
            id="v3", name="MidVax", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=10, reference_table=[],
            q10_value=2.0, ideal_temp=5.0
        )
        mock_reader.get_vaccines.return_value = [vaccine]
        
        # Setup: Readings causing >50% HER.
        # Segment 1: 60 hours at 15°C. Degradation = 60 * 2 = 120 hours.
        # Segment 2: 10 hours at 5°C. Degradation = 10 * 1 = 10 hours.
        # Total degradation = 130 hours.
        # Shelf life = 240 hours.
        # HER = 130 / 240 ~= 0.54. This is > 0.5, so PARTIAL.
        t0 = datetime.now()
        readings = [
            TemperatureReading("v3", 15.0, t0),
            TemperatureReading("v3", 5.0, t0 + timedelta(hours=60)),
            TemperatureReading("v3", 5.0, t0 + timedelta(hours=70)),
        ]
        mock_reader.read_all.return_value = readings
        
        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()
        
        assert len(results) == 1
        result = results[0]
        assert result.vaccine_id == "v3"
        assert result.status == VaccineStatus.PARTIAL
        assert result.her == pytest.approx(130.0 / 240.0)

    def test_execute_with_no_readings_for_vaccine(self, mock_reader, mock_repo):
        """
        Tests that a vaccine is not included in the results if it has no
        temperature readings.
        """
        vaccine = Vaccine(
            id="v4", name="NoDataVax", 
            full_loss_threshold_low=0.0, full_loss_threshold_high=40.0, 
            shelf_life_days=10, reference_table=[]
        )
        mock_reader.get_vaccines.return_value = [vaccine]
        mock_reader.read_all.return_value = [] # No readings at all
        
        uc = EvaluateColdChainSafetyUC(mock_reader, mock_repo)
        results = uc.execute()
        
        assert len(results) == 0