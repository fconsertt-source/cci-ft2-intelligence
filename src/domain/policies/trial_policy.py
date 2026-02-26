from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta  # ← timedelta مُستورد بشكل صحيح
from enum import Enum
from typing import Optional

class TrialStatus(Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TAMPERED = "TAMPERED"

@dataclass(frozen=True)
class TrialPolicy:
    installation_time: datetime
    trial_duration_days: int
    last_valid_run_time: Optional[datetime] = None

    def evaluate(self, current_time: datetime) -> TrialStatus:
        # 1. Check for rollback
        if self.last_valid_run_time and current_time < self.last_valid_run_time:
            return TrialStatus.TAMPERED

        # 2. Check trial expiry
        expiry = self.installation_time + timedelta(days=self.trial_duration_days)
        if current_time > expiry:
            return TrialStatus.EXPIRED

        # 3. All OK
        return TrialStatus.ACTIVE
