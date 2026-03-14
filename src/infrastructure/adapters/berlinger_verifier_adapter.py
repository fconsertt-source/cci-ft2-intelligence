import subprocess
import logging
import os
from pathlib import Path

from src.application.ports.official_verifier_port import OfficialVerifierPort
from src.domain.evidence.verification_result import VerificationResult, VerificationStatus
from src.infrastructure.utils.runtime_resolver import RuntimeResolver
from src.infrastructure.utils.path_resolver import get_berlinger_verifier_path
from src.infrastructure.logging import get_audit_logger

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()


class BerlingerVerifierAdapter(OfficialVerifierPort):
    """
    Infrastructure adapter for official Berlinger JAR verification.
    
    ✅ Forensic-grade: يميز بين فشل البيئة وفشل التوقيع
    ✅ Handles headless environments gracefully
    ✅ Observable: logging مفصل للتشخيص
    """
    
    def __init__(
        self,
        jar_filename: str = "verifier-3.5-basic-with-dependencies.jar",
        jvm_args: list[str] = None,
        timeout_seconds: int = 300
    ):
        self.jar_path = get_berlinger_verifier_path(jar_filename)
        self.runtime_resolver = RuntimeResolver()
        
        # ✅ JVM flags قابلة للتهيئة
        self.jvm_args = jvm_args or [
            "-Djava.awt.headless=true",
            "-Dfile.encoding=UTF-8",
            "-Duser.language=en"
        ]
        self.timeout = timeout_seconds
        
        # ✅ Pre-flight check: تحقق من توفر الـ verifier
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """تحقق مبدئي من توفر الـ verifier وقابليته للتشغيل"""
        try:
            java_exec = self.runtime_resolver.resolve_java_executable()
            cmd = [str(java_exec)] + self.jvm_args + ["-jar", str(self.jar_path), "--help"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # إذا ظهرت HeadlessException في --help، فالأداة GUI-bound
            output = (result.stdout + result.stderr).lower()
            if "headlessexception" in output:
                logger.warning("Berlinger verifier requires GUI (HeadlessException detected)")
                return False
            
            return result.returncode == 0 or "--help" in result.stdout
            
        except Exception as e:
            logger.error(f"Pre-flight check failed: {e}")
            return False
    
    def verify_file(self, file_path: Path) -> VerificationResult:
        """
        Execute official verification with forensic-grade error classification.
        """
        if not file_path.exists():
            return VerificationResult(
                status=VerificationStatus.MALFORMED_STRUCTURE,
                diagnostics=f"File not found: {file_path}"
            )

        if not self.jar_path.exists():
            return VerificationResult(
                status=VerificationStatus.SIGNATURE_MISSING,
                diagnostics=f"Verifier JAR not found: {self.jar_path}"
            )
        
        # ✅ إذا لم يكن الـ verifier متاحاً، أعد حالة واضحة (ليس CRYPTO_FAILURE)
        if not self._available:
            return VerificationResult(
                status=VerificationStatus.DECODE_ERROR,
                diagnostics="BERLINGER_VERIFIER_UNAVAILABLE: GUI required or environment issue",
                normalized_data=b""
            )

        # 1. Resolve Java Runtime
        try:
            java_executable = self.runtime_resolver.resolve_java_executable()
        except RuntimeError as e:
            return VerificationResult(
                status=VerificationStatus.DECODE_ERROR,
                diagnostics=f"Java runtime error: {e}"
            )

        # 2. Build Command with configurable JVM args
        command = [str(java_executable)] + self.jvm_args + ["-jar", str(self.jar_path), str(file_path)]

        logger.info("Executing verification: %s", " ".join(command))
        logger.debug("Verifying file: %s", file_path)

        # ✅ عزل البيئة لمنع تلوث Java
        env = dict(**os.environ)
        env.setdefault("JAVA_TOOL_OPTIONS", "")

        # 3. Execute & Capture
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                env=env
            )

            # Debug logging للتشخيص
            logger.debug("Return code: %s", result.returncode)
            logger.debug("Stdout (first 500): %s", (result.stdout or "")[:500])
            logger.debug("Stderr (first 500): %s", (result.stderr or "")[:500])

            # 4. Parse Output with forensic classification
            verification_result = self._parse_verifier_output(
                result.stdout, result.stderr, result.returncode
            )

            # 5. Audit Log
            audit_logger.info(
                "OFFICIAL_BERLINGER_VERIFICATION | File: %s | Status: %s | Verifier: %s",
                str(file_path),
                verification_result.status.value,
                str(self.jar_path)
            )

            return verification_result

        except subprocess.TimeoutExpired:
            logger.error("Verification timed out for: %s", file_path)
            return VerificationResult(
                status=VerificationStatus.DECODE_ERROR,
                diagnostics="Verification process timed out"
            )
        except Exception as e:
            logger.error("Verification failed: %s", e, exc_info=True)
            return VerificationResult(
                status=VerificationStatus.DECODE_ERROR,
                diagnostics=f"Execution error: {e}"
            )

    def _parse_verifier_output(self, stdout: str, stderr: str, returncode: int) -> VerificationResult:
        """
        Parse JAR output with forensic-grade error classification.
        
        التصنيف الجنائي:
        - DECODE_ERROR: مشكلة بيئة/تشغيل (HeadlessException, Java missing, etc.)
        - CRYPTO_FAILURE: فشل توقيع/شهادة حقيقي
        - MALFORMED_STRUCTURE: بنية ملف غير صالحة
        - SUCCESS: تحقق ناجح (مع/بدون alarm)
        """
        # ✅ None-safety + توحيد المخرجات
        stdout = stdout or ""
        stderr = stderr or ""
        output_combined = stdout + "\n" + stderr
        output_lower = output_combined.lower()
        
        # 🔴 أولوية: كشف HeadlessException كفئة خاصة (ليس crypto failure)
        if "headlessexception" in output_lower:
            return VerificationResult(
                status=VerificationStatus.DECODE_ERROR,
                diagnostics="BERLINGER_GUI_REQUIRED: HeadlessException detected - verifier needs display",
                normalized_data=output_combined.encode("utf-8", errors="replace")
            )
        
        # 🔴 كشف أخطاء البيئة الأخرى
        env_error_patterns = [
            "noclassdeffounderror", "classnotfoundexception", 
            "could not find or load main class", "unsupportedclassversionerror",
            "error: could not open", "error: unable to access"
        ]
        if any(p in output_lower for p in env_error_patterns):
            return VerificationResult(
                status=VerificationStatus.DECODE_ERROR,
                diagnostics=f"Environment error: {stderr.strip()[:200]}",
                normalized_data=output_combined.encode("utf-8", errors="replace")
            )
        
        # ✅ الحالة 1: التحقق نجح والتوقيع صالح
        # أنماط أكثر مرونة للتوقيع الصالح
        signature_valid_patterns = [
            "digital signature: ✓", "digital signature: valid",
            "signature verified", "signature: ok", "✓ valid", "valid signature"
        ]
        
        if any(pattern in output_lower for pattern in signature_valid_patterns):
            # تحقق من وجود alarm
            alarm_patterns = [
                "alarm status: ✗", "alarm: detected", "alarm triggered", "✗ alarm"
            ]
            
            if any(p in output_lower for p in alarm_patterns):
                return VerificationResult(
                    status=VerificationStatus.SUCCESS,
                    diagnostics="SIGNATURE_VALID_BUT_ALARM_DETECTED: Cold chain excursion detected",
                    normalized_data=output_combined.encode("utf-8", errors="replace")
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.SUCCESS,
                    diagnostics="SIGNATURE_VALID_NO_ALARMS",
                    normalized_data=output_combined.encode("utf-8", errors="replace")
                )

        # ❌ الحالة 2: فشل تقني في التحقق (crypto حقيقي)
        if returncode != 0:
            crypto_patterns = ["signature", "crypto", "verification failed", "certificate", "pkcs", "invalid signature"]
            if any(kw in output_lower for kw in crypto_patterns):
                return VerificationResult(
                    status=VerificationStatus.CRYPTO_FAILURE,
                    diagnostics=stderr.strip()[:500],
                    normalized_data=output_combined.encode("utf-8", errors="replace")
                )
            
            malformed_patterns = ["malformed", "format", "parse error", "invalid structure", "unexpected token"]
            if any(kw in output_lower for kw in malformed_patterns):
                return VerificationResult(
                    status=VerificationStatus.MALFORMED_STRUCTURE,
                    diagnostics=stderr.strip()[:500],
                    normalized_data=output_combined.encode("utf-8", errors="replace")
                )

        # فشل عام - نرجع مخرجات كاملة للتحليل
        return VerificationResult(
            status=VerificationStatus.DECODE_ERROR,
            diagnostics=f"Unrecognized output (returncode={returncode})\nStdout: {stdout[:300]}\nStderr: {stderr[:300]}",
            normalized_data=output_combined.encode("utf-8", errors="replace")
        )
