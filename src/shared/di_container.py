#!/usr/bin/env python3
"""
حاوية حقن التبعيات (Dependency Injection Container)

✅ نظيفة من التكرار
✅ تبني مكونات حقيقية (ليس Mocks في الإنتاج)
✅ قابلة للتوسع
✅ متوافقة مع Clean Architecture
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.infrastructure.adapters.ledger_writer_adapter import \
    HashChainedLedgerWriter

T = TypeVar('T')
logger = logging.getLogger(__name__)


class DIContainer:
    """حاوية بسيطة لحقن التبعيات للإنتاج."""

    def __init__(self):
        self._services: dict[Type, Any] = {}
        self._factories: dict[Type, callable] = {}

    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """تسجيل خدمة كنسخة وحيدة (Singleton)"""
        self._services[interface] = implementation

    def register_factory(self, interface: Type[T], factory: callable) -> None:
        """تسجيل خدمة عبر مصنع (Factory)"""
        self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """حل واجهة والحصول على التطبيق."""
        if interface in self._services:
            return self._services[interface]

        if interface in self._factories:
            instance = self._factories[interface](self)
            self._services[interface] = instance
            return instance

        raise ValueError(f"No registration found for {interface}")

    def is_registered(self, interface: Type[T]) -> bool:
        """التحقق مما إذا كانت الواجهة مسجلة"""
        return interface in self._services or interface in self._factories

    def clear(self) -> None:
        """مسح جميع التسجيلات (للاختبارات فقط)"""
        self._services.clear()
        self._factories.clear()


container = DIContainer()


def configure_ledger(
    ledger_path: Optional[Path] = None, state_path: Optional[Path] = None
) -> HashChainedLedgerWriter:
    """تهيئة وتسجيل LedgerWriter في الحاوية."""
    if ledger_path is None:
        ledger_path = Path('data/ledger/verification_ledger.jsonl')
    else:
        ledger_path = Path(ledger_path)

    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    ledger_writer = HashChainedLedgerWriter(
        ledger_path=ledger_path, state_path=state_path
    )

    container.register_singleton(LedgerWriterPort, ledger_writer)
    return ledger_writer


def _resolve_or_fail(port_type: Type[T]) -> T:
    """حل dependency من الحاوية مع فشل صريح ورسالة سياقية."""
    try:
        return container.resolve(port_type)
    except ValueError as e:
        logger.critical("DI misconfiguration: %s not registered", port_type.__name__)
        raise RuntimeError(
            f"DI misconfiguration: {port_type.__name__} is not registered. "
            "Check your container setup."
        ) from e


def build_generate_device_report_uc(
    device_repository: Optional[Any] = None,
    vaccine_specifications: Optional[Any] = None,
    regulatory_decision_service: Optional[Any] = None,
    estimator: Optional[Any] = None,
    validator: Optional[Any] = None,
    license_guard: Optional[Any] = None,
    data_path: Optional[Path] = None,
):
    """
    بناء Use Case حقيقي لتوليد تقرير الجهاز.

    ✅ للإنتاج فقط – لا Mocks
    إذا لم تُمرر dependency، تُحل من الحاوية.
    إذا لم تكن مسجلة، ترفع RuntimeError.
    """
    from src.application.ports.device_repository_port import \
        DeviceRepositoryPort
    from src.application.ports.vaccine_specification_port import \
        VaccineSpecificationPort
    from src.application.ports.validation_protocol_port import \
        ValidationProtocolPort
    from src.application.security.license_guard import LicenseGuard
    from src.application.use_cases.generate_device_report_uc import \
        GenerateDeviceReportUseCase
    from src.domain.services.regulatory_decision_service import \
        RegulatoryDecisionService
    from src.domain.services.thermal_degradation_estimator import \
        ThermalDegradationEstimator

    if device_repository is None:
        device_repository = _resolve_or_fail(DeviceRepositoryPort)
    if vaccine_specifications is None:
        vaccine_specifications = _resolve_or_fail(VaccineSpecificationPort)
    if regulatory_decision_service is None:
        regulatory_decision_service = _resolve_or_fail(RegulatoryDecisionService)
    if estimator is None:
        estimator = _resolve_or_fail(ThermalDegradationEstimator)
    if validator is None:
        validator = _resolve_or_fail(ValidationProtocolPort)
    if license_guard is None:
        license_guard = _resolve_or_fail(LicenseGuard)

    return GenerateDeviceReportUseCase(
        device_repository=device_repository,
        vaccine_specifications=vaccine_specifications,
        regulatory_decision_service=regulatory_decision_service,
        estimator=estimator,
        validator=validator,
        license_guard=license_guard,
        data_path=data_path,
    )


def reset_container() -> None:
    """إعادة تعيين الحاوية (للاختبارات فقط)."""
    container.clear()


def get_container() -> DIContainer:
    """الحصول على الحاوية العالمية"""
    return container
