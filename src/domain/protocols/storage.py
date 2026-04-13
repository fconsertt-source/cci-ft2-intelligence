"""
storage.py
----------
عقد التخزين الوحيد المسموح للـ Domain بالتعامل معه.
لا يحتوي على أي استيراد من pandas أو pyarrow.
"""

from __future__ import annotations

from typing import Protocol, Iterator, Dict, Any, List, Optional, runtime_checkable


@runtime_checkable
class StorageProtocol(Protocol):
    """
    واجهة تخزين الجلسات.

    القاعدة الصارمة:
        - كل دالة تأخذ/تعيد بيانات خام (dict, iterator) فقط.
        - لا DataFrame، لا Table، لا أي نوع خارجي.
    """

    def write_session(
        self,
        session_id: str,
        readings: Iterator[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        يكتب جلسة قراءات بشكل تدفقي.

        Args:
            session_id: معرف فريد للجلسة، مثل "FT2-001_2025-04-06T08-00".
            readings:   مولِّد (generator) من القواميس - لا يُستهلَك قبل الاستدعاء.
            metadata:   بيانات تعريفية اختيارية (device_id, center, ...).

        Returns:
            المسار الكامل للملف المكتوب.

        Raises:
            SchemaMismatchError: إذا تغيّرت أعمدة الدفعات أثناء الكتابة.
            StorageWriteError:   لأي خطأ في الكتابة.
        """
        ...

    def read_session(
        self,
        session_id: str,
        columns: Optional[List[str]] = None,
        batch_size: int = 5_000,
    ) -> Iterator[Dict[str, Any]]:
        """
        يقرأ الجلسة تدفقياً صفاً صفاً.

        Args:
            session_id: معرف الجلسة.
            columns:    أسماء الأعمدة المطلوبة فقط (None = كل الأعمدة).
            batch_size: حجم الدفعة الداخلية لـ PyArrow (لا يؤثر على الناتج الخارجي).

        Yields:
            قاموس واحد لكل قراءة.

        Raises:
            SessionNotFoundError: إذا لم توجد الجلسة.
        """
        ...

    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """
        يعيد بيانات التعريف دون فتح ملف البيانات الضخم.

        Returns:
            قاموس يحتوي على: session_id, rows, created_at, schema_fields,
            checksum (إن وُجد), user_metadata.
            قاموس فارغ إذا لم توجد الجلسة.
        """
        ...

    def verify_integrity(self, session_id: str, strict: bool = False) -> bool:
        """
        يتحقق من سلامة ملف الجلسة.

        Args:
            strict: False → قراءة رأس الملف فقط (سريع، < 10ms).
                    True  → حساب SHA-256 كامل (آمن لكن أبطأ).

        Returns:
            True إذا كان الملف سليماً.
        """
        ...

    def delete_session(self, session_id: str) -> bool:
        """
        يحذف ملف الجلسة وملف metadata المرافق.

        Returns:
            True دائماً (حتى لو لم يكن الملف موجوداً).
        """
        ...