# src/domain/services/her_calculator_service.py
from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from src.domain.entities.temperature_reading import TemperatureReading
from src.domain.value_objects.ccm_result import CCMResult
from src.domain.value_objects.her_result import HERResult


@runtime_checkable
class HerCalculatorService(Protocol):
    """
    Strategy interface for HER calculation.
    مستقل تماماً عن CCM — يُنفَّذ بشكل منفصل.
    """

    def calculate(self, readings: List[TemperatureReading]) -> HERResult:
        """
        حساب Heat Exposure Ratio من قراءات درجة الحرارة.

        Args:
            readings: قراءات درجة الحرارة المُجمَّعة من جهاز FT2

        Returns:
            HERResult: نتيجة نقية — بدون قرار ACCEPT/REJECT
        """
        ...


@runtime_checkable
class CcmCalculatorService(Protocol):
    """
    Strategy interface for CCM calculation.
    مستقل تماماً عن HER — يُنفَّذ بشكل منفصل.
    """

    def calculate(self, readings: List[TemperatureReading]) -> CCMResult:
        """
        حساب Cold Chain Monitor من قراءات درجة الحرارة.

        Args:
            readings: قراءات درجة الحرارة المُجمَّعة من جهاز FT2

        Returns:
            CCMResult: نتيجة نقية — بدون قرار ACCEPT/REJECT
        """
        ...
