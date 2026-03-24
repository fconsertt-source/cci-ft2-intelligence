#!/usr/bin/env python3
"""
حاوية حقن التبعيات (Dependency Injection Container) v2.2
✅ نظيفة من التكرار
✅ تبني مكونات حقيقية (ليس Mocks في الإنتاج)
✅ قابلة للتوسع
✅ متوافقة مع Clean Architecture
✅ مكونات أمنية مدمجة
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.infrastructure.adapters.ledger_writer_adapter import \
    HashChainedLedgerWriter

T = TypeVar("T")
logger = logging.getLogger(__name__)


class DIContainer:
    """حاوية بسيطة لحقن التبعيات للإنتاج."""

    def __init__(self):
        self._services: dict[Type, Any] = {}
        self._factories: dict[Type, callable] = {}
        self._initialized: bool = False

    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        self._services[interface] = implementation

    def register_factory(self, interface: Type[T], factory: callable) -> None:
        self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        if interface in self._services:
            return self._services[interface]
        if interface in self._factories:
            instance = self._factories[interface](self)
            self._services[interface] = instance
            return instance
        raise ValueError(f"No registration found for {interface}")

    def is_registered(self, interface: Type[T]) -> bool:
        return interface in self._services or interface in self._factories

    def clear(self) -> None:
        self._services.clear()
        self._factories.clear()
        self._initialized = False

    def initialize_security_components(self) -> None:
        """تهيئة المكونات الأمنية في الحاوية."""
        if self._initialized:
            return

        logger.info("Initializing security components...")

        from src.application.security.error_handler import SecureErrorHandler
        from src.application.security.secure_logger import SecureAuditLogger

        log_file = os.getenv("CCIF_AUDIT_LOG_FILE", "logs/security_audit.log")
        audit_logger = SecureAuditLogger(log_file=log_file)
        self.register_singleton(SecureAuditLogger, audit_logger)
        logger.info("SecureAuditLogger registered")

        env = os.getenv("CCIF_ENVIRONMENT", "development")
        error_handler = SecureErrorHandler(environment=env, audit_logger=audit_logger)
        self.register_singleton(SecureErrorHandler, error_handler)
        logger.info("SecureErrorHandler registered")

        self._initialized = True
        logger.info("Security components initialization complete")


container = DIContainer()


def configure_ledger(
    ledger_path: Optional[Path] = None, state_path: Optional[Path] = None
) -> HashChainedLedgerWriter:
    if ledger_path is None:
        ledger_path = Path("data/ledger/verification_ledger.jsonl")
    else:
        ledger_path = Path(ledger_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_writer = HashChainedLedgerWriter(
        ledger_path=ledger_path, state_path=state_path
    )
    container.register_singleton(LedgerWriterPort, ledger_writer)
    return ledger_writer


def configure_security() -> None:
    """تهيئة جميع المكونات الأمنية في الحاوية."""
    container.initialize_security_components()


def reset_container() -> None:
    container.clear()


def get_container() -> DIContainer:
    return container
