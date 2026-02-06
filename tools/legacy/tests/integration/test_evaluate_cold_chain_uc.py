import pytest
from unittest.mock import MagicMock
from src.application.use_cases.evaluate_cold_chain_safety_uc import EvaluateColdChainSafetyUC
from src.application.dtos.analysis_result_dto import AnalysisResultDTO, VaccineStatus

class TestEvaluateColdChainSafetyUC:

    def test_uc_executes_and_returns_dto(self):
        # Arrange
        # Mock the reader (port) to return some dummy data
        mock_reader = MagicMock()
        mock_reader.get_vaccines.return_value = (
            {"id": "VAC001", "q10_value": 1.8, "ideal_temp": 5.0, "shelf_life_days": 30.0},
        )
        mock_reader.read_all.return_value = () # No readings for simplicity

        # Instantiate the legacy Use Case with the mocked dependency
        uc = EvaluateColdChainSafetyUC(reader=mock_reader)

        # Act
        response = uc.execute()

        # Assert
        # The legacy UC wraps the pure UC, so we expect the pure response structure
        assert hasattr(response, "results")
        assert isinstance(response.results, tuple)
        assert len(response.results) > 0
        assert response.results[0].vaccine_id == "VAC001"