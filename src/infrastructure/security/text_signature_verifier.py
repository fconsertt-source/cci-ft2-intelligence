# src/infrastructure/security/text_signature_verifier.py
"""التحقق من توقيع ملفات Berlinger Q-tag (ECDSA/secp256r1)"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from src.domain.evidence.verification_result import VerificationStatus, VerificationResult
from src.application.ports.text_signature_verifier_port import ITextSignatureVerifier
from src.application.ports.keyring_port import KeyRingPort

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import utils as asym_utils
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import logging

logger = logging.getLogger(__name__)

# نمط البحث عن قسم التوقيع
CERT_PATTERN = re.compile(rb"\nCert:\r?\n")
MAX_TXT_SIZE = 2 * 1024 * 1024  # 2 MB


class TextSignatureVerifier(ITextSignatureVerifier):
    """التحقق من توقيع ملفات Berlinger Q-tag"""

    def __init__(self, keyring: KeyRingPort) -> None:
        self._keyring = keyring

    # =========================================
    # PUBLIC API
    # =========================================
    def verify(self, raw_content: bytes) -> VerificationResult:
        """التحقق من التوقيع في ملف TXT"""
        try:
            # حماية من هجمات حجم الملف
            if len(raw_content) > MAX_TXT_SIZE:
                return VerificationResult(
                    status=VerificationStatus.SIZE_LIMIT_EXCEEDED,
                    diagnostics="TXT size exceeds hard limit",
                )

            # البحث عن قسم التوقيع
            matches = list(CERT_PATTERN.finditer(raw_content))
            if not matches:
                return VerificationResult(
                    status=VerificationStatus.SIGNATURE_MISSING,
                    diagnostics="Cert section not found",
                )
            if len(matches) != 1:
                return VerificationResult(
                    status=VerificationStatus.MALFORMED_STRUCTURE,
                    diagnostics=f"Multiple Cert sections detected: {len(matches)}",
                )

            cert_match = matches[0]
            cert_start = cert_match.start()
            cert_end = cert_match.end()

            data_part = raw_content[:cert_start]
            cert_part = raw_content[cert_end:]

            # توحيد البيانات حسب مواصفات Berlinger
            normalized = self._normalize_bytes(data_part)

            # تحليل قسم التوقيع
            parsed = self._parse_cert(cert_part)
            if parsed is None:
                return VerificationResult(
                    status=VerificationStatus.MALFORMED_STRUCTURE,
                    diagnostics="Failed to parse Cert section",
                )

            issuer, public_key_hex, signature_hex = parsed

            # التحقق من التوقيع باستخدام البايتات الموحّدة مباشرة
            is_valid = self._verify_ecdsa_signature(
                data_bytes=normalized,
                signature_hex=signature_hex,
                public_key_hex=public_key_hex
            )

            if not is_valid:
                return VerificationResult(
                    status=VerificationStatus.CRYPTO_FAILURE,
                    issuer=issuer,
                    diagnostics="ECDSA verification failed",
                )

            # النجاح
            return VerificationResult(
                status=VerificationStatus.SUCCESS,
                issuer=issuer,
                normalized_data=normalized,
                signature_hex=signature_hex,
                diagnostics=None,
            )

        except Exception as exc:
            logger.warning(f"فشل التحقق من التوقيع: {exc}")
            return VerificationResult(
                status=VerificationStatus.DECODE_ERROR,
                diagnostics=str(exc),
            )

    # =========================================
    # INTERNALS
    # =========================================
    @staticmethod
    def _normalize_bytes(data: bytes) -> bytes:
        """
        Berlinger normalization spec:
        - تحويل كل نهايات السطر إلى LF
        - إزالة الفراغات أو التابات من نهاية كل سطر
        - إزالة الأسطر الفارغة في النهاية
        - إضافة سطر جديد واحد فقط في النهاية
        """
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        lines = [line.rstrip(b" \t") for line in data.split(b"\n")]
        while lines and lines[-1] == b"":
            lines.pop()
        return b"\n".join(lines) + b"\n"

    @staticmethod
    def _parse_cert(cert_part: bytes) -> Optional[Tuple[str, str, str]]:
        """تحليل قسم التوقيع ECDSA"""
        try:
            text = cert_part.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            return None

        issuer_match = re.search(r"Issuer:\s*(.+)$", text, re.MULTILINE)
        if not issuer_match:
            return None
        issuer = issuer_match.group(1).strip()

        pubkey_match = re.search(r"Public Key:\s*([0-9a-fA-F]{128})", text, re.MULTILINE)
        if not pubkey_match:
            return None
        public_key_hex = pubkey_match.group(1).strip()

        sig_lines = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('Sig:') and not line.startswith('Sig Cert:'):
                sig_lines.append(line)

        if not sig_lines:
            return None

        sig_line = sig_lines[0]
        parts = sig_line.split(':', 1)
        if len(parts) != 2:
            return None
        signature_hex = parts[1].strip()

        if len(signature_hex) != 128 or not re.fullmatch(r'[0-9a-fA-F]{128}', signature_hex):
            return None

        return issuer, public_key_hex, signature_hex

    def _verify_ecdsa_signature(self, data_bytes: bytes, signature_hex: str, public_key_hex: str) -> bool:
        """التحقق من توقيع ECDSA باستخدام DER"""
        try:
            if len(public_key_hex) != 128 or len(signature_hex) != 128:
                return False

            x = int(public_key_hex[:64], 16)
            y = int(public_key_hex[64:], 16)
            public_key = ec.EllipticCurvePublicNumbers(
                x=x, y=y, curve=ec.SECP256R1()
            ).public_key(default_backend())

            raw_signature = bytes.fromhex(signature_hex)
            der_signature = self._raw_to_der(raw_signature)

            public_key.verify(
                signature=der_signature,
                data=data_bytes,  # ← استخدم البايتات الموحّدة مباشرة
                signature_algorithm=ec.ECDSA(hashes.SHA256())
            )
            return True

        except (InvalidSignature, ValueError, TypeError) as e:
            logger.debug(f"فشل التحقق من التوقيع: {e}")
            return False

    @staticmethod
    def _raw_to_der(raw_signature: bytes) -> bytes:
        """تحويل توقيع ECDSA من Raw (r+s) إلى DER"""
        if len(raw_signature) != 64:
            raise ValueError(f"التوقيع الخام يجب أن يكون 64 بايت، وجد: {len(raw_signature)}")
        r = int.from_bytes(raw_signature[:32], byteorder='big')
        s = int.from_bytes(raw_signature[32:], byteorder='big')
        return asym_utils.encode_dss_signature(r, s)