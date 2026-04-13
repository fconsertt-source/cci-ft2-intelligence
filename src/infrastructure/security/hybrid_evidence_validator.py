#!/usr/bin/env python3
"""
Hybrid Evidence Validator - محقق الأدلة الهجين
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.application.ports.ledger_writer_port import LedgerWriterPort
from src.application.ports.official_verifier_port import OfficialVerifierPort
from src.application.ports.pdf_extractor_port import PdfExtractorPort
from src.domain.enums.ledger_event import LedgerEvent
from src.domain.evidence.cross_validation_result import CrossValidationResult
from src.domain.evidence.evidence_integrity_report import (
    EvidenceGrade, EvidenceIntegrityReport)
from src.domain.evidence.verification_result import (VerificationResult,
                                                     VerificationStatus)

logger = logging.getLogger(__name__)


class HybridEvidenceValidator:
    """محقق الأدلة الهجين للتحقق الجنائي من ملفات FT2."""

    TEMP_TOLERANCE = 0.5
    TIMESTAMP_TOLERANCE_SECONDS = 120

    def __init__(
        self,
        text_verifier: OfficialVerifierPort,
        pdf_extractor: PdfExtractorPort,
        ledger_writer: Optional[LedgerWriterPort] = None,
        temp_tolerance: float = 0.5,
        timestamp_tolerance: int = 120,
    ):
        self.text_verifier = text_verifier
        self.pdf_extractor = pdf_extractor
        self.ledger_writer = ledger_writer
        self.temp_tolerance = temp_tolerance
        self.timestamp_tolerance = timestamp_tolerance

    def validate(
        self, txt_path: Path, pdf_path: Optional[Path] = None
    ) -> EvidenceIntegrityReport:
        """التحقق الهجين من الدليل."""
        txt_path = Path(txt_path)
        pdf_path = Path(pdf_path) if pdf_path else None

        logger.info("Starting hybrid validation: %s", txt_path.name)

        if not txt_path.exists():
            return self._build_rejection_report(
                txt_path,
                VerificationStatus.MALFORMED_STRUCTURE,
                CrossValidationResult.FILE_MISSING,
                f"TXT file not found: {txt_path}",
            )

        if pdf_path and not pdf_path.exists():
            logger.warning("PDF not found, proceeding with TXT-only validation")
            pdf_path = None

        txt_verification = self.text_verifier.verify_file(txt_path)
        txt_verification = self._ensure_normalized_data_bytes(txt_verification)

        if txt_verification.status in [
            VerificationStatus.CRYPTO_FAILURE,
            VerificationStatus.INVALID_SIGNATURE,
        ]:
            logger.warning(
                "توقيع غير صالح - رفض المعالجة: %s, الحالة: %s",
                txt_path.name,
                txt_verification.status,
            )
            return self._build_rejection_report(
                txt_path,
                txt_verification.status,
                CrossValidationResult.SIGNATURE_INVALID,
                txt_verification.diagnostics,
            )

        pdf_data = None
        if pdf_path:
            try:
                pdf_data = self.pdf_extractor.extract(pdf_path)
            except Exception as e:
                logger.error("PDF extraction failed: %s", e)
                pdf_data = None

        comparison_result = self._compare_data(txt_verification, pdf_data)

        report = self._build_integrity_report(
            txt_path=txt_path,
            txt_verification=txt_verification,
            pdf_data=pdf_data,
            comparison_result=comparison_result,
        )

        if self.ledger_writer:
            self._log_to_ledger(txt_path, report)

        return report

    def _ensure_normalized_data_bytes(
        self, verification: VerificationResult
    ) -> VerificationResult:
        """ضمان أن normalized_data هي bytes صالحة للـ hashing."""
        raw = verification.normalized_data

        if raw is None:
            logger.warning("normalized_data is None, using empty bytes")
            object.__setattr__(verification, "normalized_data", b"")
            return verification

        if isinstance(raw, (bytes, bytearray, memoryview)):
            return verification

        if isinstance(raw, str):
            logger.warning("normalized_data is str, encoding to bytes")
            object.__setattr__(
                verification, "normalized_data", raw.encode("utf-8", errors="replace")
            )
            return verification

        logger.warning("normalized_data is unexpected type %s, using repr", type(raw))
        object.__setattr__(
            verification, "normalized_data", repr(raw).encode("utf-8", errors="replace")
        )
        return verification

    def _compare_data(
        self, txt_verification: VerificationResult, pdf_data: Optional[Dict[str, Any]]
    ) -> CrossValidationResult:
        """مقارنة البيانات بين TXT و PDF."""
        if pdf_data is None:
            logger.info("TXT-only validation mode - skipping PDF comparison")
            return CrossValidationResult.TXT_ONLY

        mismatches = []

        # 1. مقارنة serial
        txt_serial = getattr(txt_verification, "serial", None)
        pdf_serial = pdf_data.get("serial")
        if txt_serial and pdf_serial and txt_serial != pdf_serial:
            mismatches.append(
                f"Serial mismatch: TXT={txt_serial}, PDF={pdf_serial}"
            )

        # 2. مقارنة درجات الحرارة
        pdf_min = pdf_data.get("min_temp")
        pdf_max = pdf_data.get("max_temp")
        txt_min = getattr(txt_verification, "min_temperature", None)
        txt_max = getattr(txt_verification, "max_temperature", None)

        if pdf_min is not None and txt_min is not None:
            if abs(float(pdf_min) - float(txt_min)) > self.temp_tolerance:
                mismatches.append(
                    f"Min temp mismatch: TXT={txt_min}, PDF={pdf_min}"
                )

        if pdf_max is not None and txt_max is not None:
            if abs(float(pdf_max) - float(txt_max)) > self.temp_tolerance:
                mismatches.append(
                    f"Max temp mismatch: TXT={txt_max}, PDF={pdf_max}"
                )

        # 3. مقارنة الطوابع الزمنية
        pdf_start = pdf_data.get("start_date")
        pdf_stop = pdf_data.get("stop_date")
        txt_start = getattr(txt_verification, "start_date", None)
        txt_stop = getattr(txt_verification, "stop_date", None)

        if pdf_start and txt_start and str(pdf_start) != str(txt_start):
            mismatches.append(
                f"Start date mismatch: TXT={txt_start}, PDF={pdf_start}"
            )

        if pdf_stop and txt_stop and str(pdf_stop) != str(txt_stop):
            mismatches.append(
                f"Stop date mismatch: TXT={txt_stop}, PDF={pdf_stop}"
            )

        if mismatches:
            logger.warning("Cross-validation found %d mismatch(s): %s",
                           len(mismatches), "; ".join(mismatches))
            return CrossValidationResult.MINOR_MISMATCH

        return CrossValidationResult.MATCH

    def _build_rejection_report(
        self,
        txt_path: Path,
        signature_status: VerificationStatus,
        cross_check_result: CrossValidationResult,
        details: str,
    ) -> EvidenceIntegrityReport:
        """بناء تقرير رفض موحد"""
        serial = (
            getattr(txt_path, "stem", "UNKNOWN").split("_")[0]
            if txt_path
            else "UNKNOWN"
        )

        return EvidenceIntegrityReport(
            device_id=serial if serial != "UNKNOWN" else "UNKNOWN",
            serial=serial,
            signature_status=signature_status,
            cross_check_result=cross_check_result,
            overall_grade=EvidenceGrade.F,
            is_rejected=True,
            details=f"تم رفض الأدلة: {details}",
        )

    def _build_integrity_report(
        self,
        txt_path: Path,
        txt_verification: VerificationResult,
        pdf_data: Optional[Dict[str, Any]],
        comparison_result: CrossValidationResult,
    ) -> EvidenceIntegrityReport:
        """بناء تقرير السلامة الكامل"""
        serial = getattr(txt_verification, "serial", "UNKNOWN")

        if comparison_result == CrossValidationResult.MATCH:
            grade = EvidenceGrade.A
        elif comparison_result == CrossValidationResult.TXT_ONLY:
            grade = EvidenceGrade.B
        elif comparison_result == CrossValidationResult.MINOR_MISMATCH:
            grade = EvidenceGrade.C
        else:
            grade = EvidenceGrade.F

        txt_hash = hashlib.sha256(txt_verification.normalized_data).hexdigest()

        return EvidenceIntegrityReport(
            device_id=serial if serial != "UNKNOWN" else "UNKNOWN",
            serial=serial,
            signature_status=txt_verification.status,
            cross_check_result=comparison_result,
            overall_grade=grade,
            is_rejected=(grade == EvidenceGrade.F),
            details=txt_verification.diagnostics,
            txt_hash=txt_hash,
            min_temperature=pdf_data.get("min_temp") if pdf_data else None,
            max_temperature=pdf_data.get("max_temp") if pdf_data else None,
            avg_temperature=pdf_data.get("avg_temp") if pdf_data else None,
        )

    def _log_to_ledger(self, txt_path: Path, report: EvidenceIntegrityReport) -> None:
        """تسجيل نتيجة التحقق في Ledger"""
        try:
            event_type = (
                LedgerEvent.AUTHENTICITY_VERIFIED
                if not report.is_rejected
                else LedgerEvent.AUTHENTICITY_FAILED
            )

            self.ledger_writer.append(
                event_type=event_type,
                file_hash=report.txt_hash if hasattr(report, "txt_hash") else "N/A",
                event_id=f"hybrid-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                ft2_serial=report.serial,
                authenticity_status=report.signature_status.value,
                thermal_status=report.overall_grade.value,
                alarm_detected=report.is_rejected,
                source_path=str(txt_path),
            )
        except Exception as e:
            logger.error("Failed to log to ledger: %s", e)
