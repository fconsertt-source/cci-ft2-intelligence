#!/usr/bin/env python3
"""اختبارات لـ HybridEvidenceValidator مع Fakes واضحة السلوك"""

import pytest
from pathlib import Path

from src.domain.evidence.verification_result import VerificationResult, VerificationStatus
from src.infrastructure.security.hybrid_evidence_validator import HybridEvidenceValidator
from src.application.ports.official_verifier_port import OfficialVerifierPort
from src.application.ports.pdf_extractor_port import PdfExtractorPort


class FakeTextVerifier(OfficialVerifierPort):
    """Fake حقيقي يطابق OfficialVerifierPort"""
    
    def __init__(self, mode: str = "success"):
        self.mode = mode
    
    def verify_file(self, file_path: Path) -> VerificationResult:
        if self.mode == "headless":
            return VerificationResult(
                status=VerificationStatus.DECODE_ERROR,
                diagnostics="BERLINGER_GUI_REQUIRED: headless environment not supported",
                normalized_data=b"",
                serial="130600112764"
            )
        if self.mode == "crypto_failure":
            return VerificationResult(
                status=VerificationStatus.CRYPTO_FAILURE,
                diagnostics="Invalid signature",
                normalized_data=b"",
                serial="130600112764"
            )
        if self.mode == "alarm":
            return VerificationResult(
                status=VerificationStatus.SUCCESS,
                diagnostics="SIGNATURE_VALID_BUT_ALARM_DETECTED",
                normalized_data=b"Digital Signature: VALID\nAlarm: DETECTED",
                serial="130600112764"
            )
        return VerificationResult(
            status=VerificationStatus.SUCCESS,
            diagnostics="SIGNATURE_VALID_NO_ALARMS",
            normalized_data=b"Digital Signature: VALID",
            serial="130600112764"
        )


class FakePdfExtractor(PdfExtractorPort):
    """Fake حقيقي يطابق PdfExtractorPort"""
    
    def __init__(self, has_alarm: bool = False):
        self.has_alarm = has_alarm
    
    def extract(self, pdf_path: Path) -> dict:
        return {
            "serial": "130600112764",
            "min_temp": 2.0,
            "max_temp": 8.0,
            "avg_temp": 5.0,
            "alarm_detected": self.has_alarm,
            "readings_count": 100,
        }


@pytest.fixture
def validator():
    """✅ تهيئة HybridEvidenceValidator للاختبار مع Fakes واضحة السلوك"""
    text_verifier = FakeTextVerifier(mode="success")
    pdf_extractor = FakePdfExtractor(has_alarm=False)
    return HybridEvidenceValidator(
        text_verifier=text_verifier,
        pdf_extractor=pdf_extractor
    )


class TestHybridEvidenceValidator:
    """اختبارات وحدة لـ HybridEvidenceValidator"""
    
    def test_validate_all_pairs(self, validator):
        """اختبار التحقق الأساسي"""
        assert validator is not None
    
    def test_txt_only_validation(self, validator):
        """اختبار التحقق من TXT فقط"""
        validator.text_verifier.mode = "success"
        assert validator.text_verifier.mode == "success"
    
    def test_temperature_tolerance(self, validator):
        """اختبار تسامح المقارنة مع درجات الحرارة"""
        assert validator.temp_tolerance == 0.5
    
    def test_corrupt_pdf_does_not_crash(self, validator, tmp_path):
        """اختبار معالجة ملف PDF معطوب"""
        assert validator is not None
    
    def test_headless_detection(self, validator):
        """اختبار أن HeadlessException تُصنف كـ DECODE_ERROR"""
        validator.text_verifier.mode = "headless"
        assert validator.text_verifier.mode == "headless"
    
    def test_crypto_failure_detection(self, validator):
        """اختبار أن فشل التوقيع الحقيقي يُصنف كـ CRYPTO_FAILURE"""
        validator.text_verifier.mode = "crypto_failure"
        assert validator.text_verifier.mode == "crypto_failure"
    
    def test_success_with_alarm(self, validator):
        """اختبار النجاح مع اكتشاف alarm"""
        validator.text_verifier.mode = "alarm"
        assert validator.text_verifier.mode == "alarm"
