import pytest
from domain.enums.file_status import FileStatus

class TestFileStatus:
    def test_is_terminal_returns_true_for_archived(self):
        assert FileStatus.ARCHIVED.is_terminal is True

    def test_is_terminal_returns_true_for_quarantined(self):
        assert FileStatus.QUARANTINED.is_terminal is True

    def test_is_terminal_returns_false_for_pending(self):
        assert FileStatus.PENDING.is_terminal is False

    def test_can_process_only_validated(self):
        assert FileStatus.VALIDATED.can_process is True
        assert FileStatus.PENDING.can_process is False
        assert FileStatus.PROCESSED.can_process is False

    def test_valid_transition_pending_to_validated(self):
        assert FileStatus.can_transition_to(FileStatus.PENDING, FileStatus.VALIDATED) is True

    def test_invalid_transition_archived_to_pending(self):
        assert FileStatus.can_transition_to(FileStatus.ARCHIVED, FileStatus.PENDING) is False

    def test_terminal_states_have_no_transitions(self):
        for terminal in (FileStatus.ARCHIVED, FileStatus.QUARANTINED):
            for target in FileStatus:
                assert FileStatus.can_transition_to(terminal, target) is False