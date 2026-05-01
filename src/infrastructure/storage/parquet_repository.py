"""
parquet_repository.py
---------------------
تطبيق StorageProtocol باستخدام PyArrow + Parquet.

القرارات التصميمية:
    1. ParquetWriter يُنشأ ويُغلق داخل write_session مباشرة (لا يُمرَّر كمعامل).
    2. المولِّد يُستهلَك مرة واحدة فقط - لا dual-read.
    3. RLock يحمي كل جلسة بشكل مستقل (لا قفل عالمي).
    4. Schema يُثبَّت من الدفعة الأولى ويُفرض على كل ما يليها.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Dict, Any, Iterator, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq

from src.domain.protocols.storage import StorageProtocol
from src.infrastructure.storage.exceptions import (
    IntegrityError,
    SchemaMismatchError,
    SessionNotFoundError,
    StorageWriteError,
)


class ParquetStorageRepository:
    """
    تطبيق StorageProtocol يكتب ملفات Parquet بشكل تدفقي حقيقي.

    Args:
        base_dir:            مجلد التخزين الجذري.
        compression:         خوارزمية الضغط ('snappy' افتراضياً، أو 'zstd').
        row_group_size:      عدد الصفوف في كل Row Group داخل ملف Parquet.
        verify_strict:       إذا True، يحسب SHA-256 عند كل كتابة ويحفظه في metadata.
    """

    # التحقق من تطبيق البروتوكول وقت التشغيل
    assert issubclass(type, type), ""  # placeholder - الفحص أدناه

    def __init__(
        self,
        base_dir: Path,
        compression: str = "snappy",
        row_group_size: int = 50_000,
        verify_strict: bool = False,
    ):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.compression = compression
        self.row_group_size = row_group_size
        self.verify_strict = verify_strict

        # قفل منفصل لكل session_id لتجنب الإقفال العالمي
        self._locks: Dict[str, threading.RLock] = {}
        self._locks_meta = threading.Lock()

    # ------------------------------------------------------------------ #
    #  الكتابة                                                             #
    # ------------------------------------------------------------------ #

    def write_session(
        self,
        session_id: str,
        readings: Iterator[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        يكتب الجلسة تدفقياً باستخدام ParquetWriter.

        الضمانات:
            - الذاكرة المستخدمة = row_group_size × حجم الصف (ثابتة).
            - Schema يُثبَّت من الدفعة الأولى.
            - الملف يُحذف تلقائياً عند أي خطأ (لا ملفات ناقصة).
        """
        lock = self._get_lock(session_id)
        path = self.base_dir / f"{session_id}.parquet"

        with lock:
            writer: Optional[pq.ParquetWriter] = None
            frozen_schema: Optional[pa.Schema] = None
            total_rows = 0

            try:
                for batch_dicts in self._chunked(readings, self.row_group_size):
                    table = pa.Table.from_pylist(batch_dicts)

                    if writer is None:
                        # الدفعة الأولى: تثبيت الـ Schema وفتح الكاتب
                        frozen_schema = table.schema
                        writer = pq.ParquetWriter(
                            path,
                            frozen_schema,
                            compression=self.compression,
                            use_dictionary=True,
                            write_statistics=True,
                        )
                    else:
                        # الدفعات التالية: فرض تطابق الـ Schema
                        if table.schema != frozen_schema:
                            raise SchemaMismatchError(
                                expected=frozen_schema.names,
                                got=table.schema.names,
                            )

                    writer.write_table(table)
                    total_rows += len(batch_dicts)

                if writer is None:
                    # المولِّد كان فارغاً تماماً
                    raise StorageWriteError(
                        f"readings iterator was empty for session '{session_id}'"
                    )

            except Exception:
                # تنظيف: لا نترك ملفاً ناقصاً على القرص
                if path.exists():
                    path.unlink()
                raise

            finally:
                if writer is not None:
                    writer.close()

            self._save_metadata(session_id, path, total_rows, frozen_schema, metadata)
            return str(path)

    # ------------------------------------------------------------------ #
    #  القراءة                                                             #
    # ------------------------------------------------------------------ #

    def read_session(
        self,
        session_id: str,
        columns: Optional[List[str]] = None,
        batch_size: int = 5_000,
    ) -> Iterator[Dict[str, Any]]:
        """
        يقرأ الجلسة تدفقياً. كل استدعاء للدالة يُعيد مولِّداً جديداً.
        الذاكرة المستخدمة = batch_size × حجم الصف (ثابتة).
        """
        path = self.base_dir / f"{session_id}.parquet"
        if not path.exists():
            raise SessionNotFoundError(session_id)

        pf = pq.ParquetFile(path)
        for record_batch in pf.iter_batches(batch_size=batch_size, columns=columns):
            # to_pydict أسرع من iterrows لأنه لا يبني DataFrame
            col_data = record_batch.to_pydict()
            num_rows = record_batch.num_rows
            for i in range(num_rows):
                yield {col: col_data[col][i] for col in col_data}

    # ------------------------------------------------------------------ #
    #  Metadata & Integrity                                                #
    # ------------------------------------------------------------------ #

    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        meta_path = self.base_dir / f"{session_id}.meta.json"
        if not meta_path.exists():
            return {}
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def verify_integrity(self, session_id: str, strict: bool = False) -> bool:
        """
        strict=False → قراءة رأس Parquet فقط (< 10ms).
        strict=True  → حساب SHA-256 كامل ومقارنته بالمحفوظ.
        """
        path = self.base_dir / f"{session_id}.parquet"
        meta_path = self.base_dir / f"{session_id}.meta.json"

        if not path.exists() or not meta_path.exists():
            return False

        # فحص الرأس دائماً
        try:
            pq.read_metadata(path)
        except Exception:
            return False

        # فحص الـ Checksum إذا طُلب
        if strict:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            expected = meta.get("checksum")
            if expected is None:
                # لم يُحسب checksum وقت الكتابة - لا يمكن التحقق
                return False
            if self._sha256(path) != expected:
                return False

        return True

    def delete_session(self, session_id: str) -> bool:
        path = self.base_dir / f"{session_id}.parquet"
        meta_path = self.base_dir / f"{session_id}.meta.json"
        path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)
        # تنظيف القفل
        with self._locks_meta:
            self._locks.pop(session_id, None)
        return True

    # ------------------------------------------------------------------ #
    #  دوال مساعدة خاصة                                                   #
    # ------------------------------------------------------------------ #

    def _get_lock(self, session_id: str) -> threading.RLock:
        """يُعيد قفلاً خاصاً بكل session_id - يُنشئه إذا لم يكن موجوداً."""
        with self._locks_meta:
            if session_id not in self._locks:
                self._locks[session_id] = threading.RLock()
            return self._locks[session_id]

    def _save_metadata(
        self,
        session_id: str,
        path: Path,
        rows: int,
        schema: pa.Schema,
        user_metadata: Optional[Dict[str, Any]],
    ) -> None:
        checksum = self._sha256(path) if self.verify_strict else None
        meta = {
            "session_id": session_id,
            "rows": rows,
            "schema_fields": schema.names,
            "schema_types": [str(t) for t in schema.types],
            "compression": self.compression,
            "checksum": checksum,
            "user_metadata": user_metadata or {},
        }
        meta_path = self.base_dir / f"{session_id}.meta.json"
        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @staticmethod
    def _chunked(
        iterator: Iterator[Dict[str, Any]], size: int
    ) -> Iterator[List[Dict[str, Any]]]:
        """يقسّم المولِّد إلى دفعات بحجم ثابت دون تحميل كل شيء في الذاكرة."""
        chunk: List[Dict[str, Any]] = []
        for item in iterator:
            chunk.append(item)
            if len(chunk) == size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(65_536), b""):
                h.update(block)
        return h.hexdigest()


# التحقق من أن الكلاس يطبق البروتوكول فعلاً
assert isinstance(
    ParquetStorageRepository(Path("/tmp/__check__")),
    StorageProtocol,
), "ParquetStorageRepository does not implement StorageProtocol"