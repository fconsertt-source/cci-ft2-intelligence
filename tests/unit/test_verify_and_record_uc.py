import hashlib
import uuid
from unittest.mock import Mock

import pytest

from src.application.use_cases.verify_and_record_uc import \
    VerifyAndRecordUseCase
from src.domain.enums.ledger_event import LedgerEvent
from src.domain.evidence.verification_result import (VerificationResult,
                                                     VerificationStatus)


class TestVerifyAndRecordUseCaseBDD:
    """
    BDD Scenarios for VerifyAndRecordUseCase.
    Ensures that verification outcomes are correctly recorded in the forensic ledger.
    """

    @pytest.fixture
    def mock_verifier(self):
        return Mock()

    @pytest.fixture
    def mock_ledger(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_verifier, mock_ledger):
        return VerifyAndRecordUseCase(mock_verifier, mock_ledger)

    def test_scenario_valid_file_verification(
        self, use_case, mock_verifier, mock_ledger, tmp_path
    ):
        """
        Scenario: A valid file is verified and recorded successfully.

        Given a valid file exists
        And the verifier confirms it is authentic
        When the verification process is executed
        Then the result should be SUCCESS
        And a 'AUTHENTICITY_VERIFIED' event should be recorded in the ledger
        And the file hash should be correctly calculated
        """
        # Given
        file_content = b"valid_data_content"
        file_path = tmp_path / "valid_evidence.txt"
        file_path.write_bytes(file_content)
        expected_hash = hashlib.sha256(file_content).hexdigest()

        # Mock successful verification
        mock_verifier.verify_file.return_value = VerificationResult(
            status=VerificationStatus.SUCCESS, diagnostics="Signature Valid"
        )

        # When
        result = use_case.execute(file_path)

        # Then
        assert result.status == VerificationStatus.SUCCESS

        # Verify ledger interaction
        mock_ledger.append.assert_called_once()
        call_kwargs = mock_ledger.append.call_args[1]

        assert call_kwargs["event_type"] == LedgerEvent.AUTHENTICITY_VERIFIED
        assert call_kwargs["file_hash"] == expected_hash
        assert call_kwargs["authenticity_status"] == VerificationStatus.SUCCESS.value
        assert call_kwargs["source_path"] == str(file_path)
        # Ensure a UUID is generated for event_id
        assert uuid.UUID(call_kwargs["event_id"])

    def test_scenario_tampered_file_verification(
        self, use_case, mock_verifier, mock_ledger, tmp_path
    ):
        """
        Scenario: A tampered file is detected and recorded as failed.

        Given a file exists
        And the verifier reports a crypto failure
        When the verification process is executed
        Then the result should be CRYPTO_FAILURE
        And a 'AUTHENTICITY_FAILED' event should be recorded in the ledger
        """
        # Given
        file_path = tmp_path / "tampered_evidence.txt"
        file_path.write_text("tampered_data")

        # Mock failed verification
        mock_verifier.verify_file.return_value = VerificationResult(
            status=VerificationStatus.CRYPTO_FAILURE, diagnostics="Hash mismatch"
        )

        # When
        result = use_case.execute(file_path)

        # Then
        assert result.status == VerificationStatus.CRYPTO_FAILURE

        # Verify ledger interaction
        mock_ledger.append.assert_called_once()
        call_kwargs = mock_ledger.append.call_args[1]

        assert call_kwargs["event_type"] == LedgerEvent.AUTHENTICITY_FAILED
        assert (
            call_kwargs["authenticity_status"]
            == VerificationStatus.CRYPTO_FAILURE.value
        )
        assert call_kwargs["source_path"] == str(file_path)

    def test_scenario_file_not_found(
        self, use_case, mock_verifier, mock_ledger, tmp_path
    ):
        """
        Scenario: File not found handling.
        """
        # Given
        missing_path = tmp_path / "non_existent.txt"
        mock_verifier.verify_file.return_value = VerificationResult(
            status=VerificationStatus.MALFORMED_STRUCTURE, diagnostics="File not found"
        )

        # When
        use_case.execute(missing_path)

        # Then
        call_kwargs = mock_ledger.append.call_args[1]
        assert call_kwargs["file_hash"] == "FILE_NOT_FOUND"
        assert call_kwargs["event_type"] == LedgerEvent.AUTHENTICITY_FAILED
