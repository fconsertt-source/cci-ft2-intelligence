import hashlib
from pathlib import Path
from typing import List

from src.domain.enums.file_status import FileStatus
from src.domain.services.device_id_extractor import DeviceIDExtractor
from src.application.ports.i_file_registry import IFileRegistry
from src.application.ports.i_center_registry import ICenterRegistry
from src.application.dtos.file_classification_result import (
    FileClassificationResult
)
from src.shared.utils.time_utils import utc_now_datetime


class ManageFileLifecycleUseCase:
    """
    Use Case: تصنيف الملفات قبل دخول Pipeline.

    المسؤولية الواحدة: يقرر مصير كل ملف.
    لا يعالج البيانات، لا يُنشئ تقارير، لا يتحدث مع Infrastructure مباشرة.

    القرارات الممكنة لكل ملف:
    1. ready_for_processing → الجهاز مسجل + الملف لم يُعالَج
    2. already_processed   → Hash موجود في Registry (Idempotency)
    3. quarantine          → جهاز غير مسجل أو hash غير صالح

    الخيارات:
    - force=True → يتجاهل Registry ويُعيد تصنيف الملفات المعالجة مسبقاً كـ ready
    """

    def __init__(
        self,
        file_registry: IFileRegistry,
        center_registry: ICenterRegistry
    ):
        # Dependency Injection — لا new() هنا
        self._file_registry = file_registry
        self._center_registry = center_registry

    def classify_files(
        self,
        file_paths: List[Path],
        run_id: str,
        force: bool = False,          # ✅ إضافة force
    ) -> FileClassificationResult:
        """
        نقطة الدخول الرئيسية للـ Use Case.
        يُصنّف كل ملف ويُعيد نتيجة موحدة.

        Args:
            file_paths: قائمة مسارات الملفات المرشحة للمعالجة.
            run_id:     معرّف التشغيل الحالي.
            force:      إذا True، يتجاهل Registry ويُعيد معالجة الملفات المكررة.
        """
        result = FileClassificationResult(run_id=run_id)
        registered_devices = self._center_registry.get_all_device_ids()

        for path in file_paths:
            self._classify_single_file(
                path, registered_devices, result, force=force  # ✅ تمرير force
            )

        return result

    def archive_processed_files(
        self,
        file_paths: List[Path],
        run_id: str
    ) -> None:
        """
        يُستدعى بعد نجاح المعالجة.
        يسجّل الملفات في Registry كـ PROCESSED.
        Infrastructure تتولى النقل الفيزيائي.
        """
        for path in file_paths:
            file_hash = self._compute_hash(path)
            device_id = DeviceIDExtractor.extract(path.name)

            self._file_registry.mark_processed(
                file_hash=file_hash,
                device_id=device_id,
                run_id=run_id,
                processed_at=utc_now_datetime()
            )

    def _classify_single_file(
        self,
        path: Path,
        registered_devices: frozenset,
        result: FileClassificationResult,
        force: bool = False,          # ✅ إضافة force
    ) -> None:
        """منطق تصنيف ملف واحد — معزول عن الباقي."""

        # الخطوة 1: حساب Hash — أي خطأ I/O يُحجر الملف فوراً
        try:
            file_hash = self._compute_hash(path)
        except (IOError, PermissionError) as e:
            result.quarantine.append((
                path,
                f"خطأ في قراءة الملف: {e}",
                f"File read error: {e}",
            ))
            return

        # الخطوة 2: فحص Idempotency — تخطي إذا مُعالَج مسبقاً (ما لم يكن force=True)
        # ✅ الإصلاح: force=True يتجاوز فحص Registry تماماً
        if not force and self._file_registry.is_processed(file_hash):
            result.already_processed.append(path)
            return

        # الخطوة 3: استخراج device_id من اسم الملف
        try:
            device_id = DeviceIDExtractor.extract(path.name)
        except ValueError as e:
            result.quarantine.append((
                path,
                f"تنسيق اسم ملف غير صالح: {e}",
                f"Invalid filename format: {e}",
            ))
            return

        # الخطوة 4: SSOT Check — الجهاز يجب أن يكون مسجلاً في YAML
        if device_id not in registered_devices:
            result.quarantine.append((
                path,
                f"جهاز غير مسجل في النظام: {device_id}",
                f"Device not registered in YAML: {device_id}",
            ))
            return

        # ✅ الملف اجتاز كل الفحوصات
        result.ready_for_processing.append(path)

    @staticmethod
    def _compute_hash(path: Path) -> str:
        """SHA-256 للمحتوى — يضمن Idempotency."""
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()