"""
test_parquet_repository.py
--------------------------
اختبارات شاملة لـ ParquetStorageRepository.

التغطية:
    ✅ الكتابة والقراءة الأساسية
    ✅ المولِّد الفارغ
    ✅ Schema Drift (الدفعات غير المتطابقة)
    ✅ الجلسة غير الموجودة
    ✅ verify_integrity بوضعيه
    ✅ حذف الجلسة
    ✅ الكتابة المتزامنة (Thread Safety)
    ✅ القراءة الجزئية (columns فقط)
    ✅ verify_strict=True (SHA-256)
    ✅ سلامة البيانات: لا فقدان صفوف
    ✅ سلامة البيانات: الأنواع محفوظة
    ✅ الملف يُحذف عند فشل الكتابة
    ✅ metadata محفوظة بشكل صحيح
    ✅ إمكانية تطبيق البروتوكول (runtime_checkable)
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Iterator, Dict, Any

import pytest
import pyarrow.parquet as pq

from src.infrastructure.storage.parquet_repository import ParquetStorageRepository
from src.infrastructure.storage.exceptions import (
    SchemaMismatchError,
    SessionNotFoundError,
    StorageWriteError,
)
from src.domain.protocols.storage import StorageProtocol


# ─────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def repo(tmp_path: Path) -> ParquetStorageRepository:
    """مستودع افتراضي بدون strict checksum."""
    return ParquetStorageRepository(tmp_path)


@pytest.fixture
def strict_repo(tmp_path: Path) -> ParquetStorageRepository:
    """مستودع بـ verify_strict=True لاختبار SHA-256."""
    return ParquetStorageRepository(tmp_path, verify_strict=True)


def _readings(n: int, base_temp: float = 5.0) -> Iterator[Dict[str, Any]]:
    """مولِّد قراءات حرارة وهمية."""
    for i in range(n):
        yield {
            "timestamp": f"2025-01-01T{i % 24:02d}:00:00Z",
            "temperature": round(base_temp + (i % 5) * 0.1, 2),
            "device_id": f"FT2-{i % 3:03d}",
        }


# ─────────────────────────────────────────────
#  1. تطبيق البروتوكول
# ─────────────────────────────────────────────

class TestProtocolCompliance:
    def test_repo_satisfies_storage_protocol(self, repo):
        """ParquetStorageRepository يجب أن يُعدّ تطبيقاً لـ StorageProtocol."""
        assert isinstance(repo, StorageProtocol)


# ─────────────────────────────────────────────
#  2. الكتابة والقراءة الأساسية
# ─────────────────────────────────────────────

class TestWriteRead:
    def test_write_returns_path(self, repo):
        path = repo.write_session("s1", _readings(10))
        assert path.endswith("s1.parquet")
        assert Path(path).exists()

    def test_read_returns_all_rows(self, repo):
        repo.write_session("s1", _readings(100))
        result = list(repo.read_session("s1"))
        assert len(result) == 100

    def test_read_preserves_values(self, repo):
        """القيم لا تتغير بين الكتابة والقراءة."""
        readings = list(_readings(5))
        repo.write_session("s1", iter(readings))
        result = list(repo.read_session("s1"))
        assert result == readings

    def test_read_preserves_types(self, repo):
        """الأنواع (float, str) يجب أن تُحفظ كما هي."""
        repo.write_session("s1", _readings(3))
        result = list(repo.read_session("s1"))
        assert isinstance(result[0]["temperature"], float)
        assert isinstance(result[0]["device_id"], str)

    def test_large_session_row_count(self, repo):
        """اختبار مع حجم يتجاوز row_group_size الافتراضي."""
        n = 120_000
        repo.write_session("large", _readings(n))
        result = list(repo.read_session("large"))
        assert len(result) == n

    def test_write_creates_meta_file(self, repo, tmp_path):
        repo.write_session("s1", _readings(10))
        assert (tmp_path / "s1.meta.json").exists()

    def test_write_parquet_is_valid(self, repo, tmp_path):
        """الملف الناتج يجب أن يكون Parquet صالحاً."""
        repo.write_session("s1", _readings(10))
        meta = pq.read_metadata(tmp_path / "s1.parquet")
        assert meta.num_rows == 10


# ─────────────────────────────────────────────
#  3. القراءة الجزئية
# ─────────────────────────────────────────────

class TestPartialRead:
    def test_read_specific_columns(self, repo):
        repo.write_session("s1", _readings(10))
        result = list(repo.read_session("s1", columns=["temperature"]))
        assert "temperature" in result[0]
        assert "device_id" not in result[0]
        assert "timestamp" not in result[0]

    def test_read_single_column_count(self, repo):
        n = 50
        repo.write_session("s1", _readings(n))
        result = list(repo.read_session("s1", columns=["temperature"]))
        assert len(result) == n


# ─────────────────────────────────────────────
#  4. حالات الحافة والأخطاء
# ─────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_iterator_raises(self, repo):
        """مولِّد فارغ يجب أن يرفع StorageWriteError."""
        with pytest.raises(StorageWriteError, match="empty"):
            repo.write_session("empty", iter([]))

    def test_empty_iterator_leaves_no_file(self, repo, tmp_path):
        """بعد الفشل، لا يجب أن يبقى ملف على القرص."""
        with pytest.raises(StorageWriteError):
            repo.write_session("empty", iter([]))
        assert not (tmp_path / "empty.parquet").exists()

    def test_read_nonexistent_session_raises(self, repo):
        with pytest.raises(SessionNotFoundError) as exc_info:
            list(repo.read_session("ghost"))
        assert exc_info.value.session_id == "ghost"

    def test_schema_drift_raises(self, repo):
        """
        إذا تغيّرت الأعمدة بين الدفعات، يجب رفع SchemaMismatchError.
        نحقق ذلك بمولِّد يُنتج صفوفاً بأعمدة مختلفة.
        """
        def drifted_readings():
            yield {"col_a": 1, "col_b": 2.0}
            yield {"col_a": 2, "col_b": 3.0}
            # الدفعة الثانية ستحتوي على عمود مختلف
            for i in range(50_001):  # يتجاوز row_group_size=50000
                yield {"col_a": i, "col_x": 99}  # ← عمود مختلف

        with pytest.raises(SchemaMismatchError) as exc_info:
            repo.write_session("drift", drifted_readings())
        assert "col_a" in str(exc_info.value)

    def test_schema_drift_leaves_no_file(self, repo, tmp_path):
        """بعد Schema Drift، لا يجب أن يبقى ملف ناقص."""
        def drifted():
            for _ in range(50_001):
                yield {"a": 1}
            yield {"b": 2}  # drift

        with pytest.raises(SchemaMismatchError):
            repo.write_session("drift", drifted())
        assert not (tmp_path / "drift.parquet").exists()


# ─────────────────────────────────────────────
#  5. Metadata
# ─────────────────────────────────────────────

class TestMetadata:
    def test_metadata_contains_row_count(self, repo):
        repo.write_session("s1", _readings(77))
        meta = repo.get_session_metadata("s1")
        assert meta["rows"] == 77

    def test_metadata_contains_schema_fields(self, repo):
        repo.write_session("s1", _readings(5))
        meta = repo.get_session_metadata("s1")
        assert "temperature" in meta["schema_fields"]
        assert "device_id" in meta["schema_fields"]

    def test_user_metadata_preserved(self, repo):
        repo.write_session(
            "s1", _readings(5),
            metadata={"center": "المركز الصحي A", "device": "FT2-001"}
        )
        meta = repo.get_session_metadata("s1")
        assert meta["user_metadata"]["center"] == "المركز الصحي A"

    def test_metadata_missing_session_returns_empty(self, repo):
        result = repo.get_session_metadata("nonexistent")
        assert result == {}


# ─────────────────────────────────────────────
#  6. التحقق من السلامة
# ─────────────────────────────────────────────

class TestIntegrity:
    def test_fast_verify_ok(self, repo):
        repo.write_session("s1", _readings(10))
        assert repo.verify_integrity("s1", strict=False) is True

    def test_fast_verify_corrupted_file(self, repo, tmp_path):
        repo.write_session("s1", _readings(10))
        # إتلاف الملف بإلحاق بيانات عشوائية
        with open(tmp_path / "s1.parquet", "ab") as f:
            f.write(b"\xff\xfe\xfd" * 100)
        assert repo.verify_integrity("s1", strict=False) is False

    def test_strict_verify_requires_checksum(self, repo):
        """
        verify_strict=False في الـ repo يعني لا checksum مُحفوظ.
        strict=True يجب أن يعيد False لأنه لا يوجد checksum للمقارنة.
        """
        repo.write_session("s1", _readings(10))
        # لا يوجد checksum → التحقق الصارم يرفض
        assert repo.verify_integrity("s1", strict=True) is False

    def test_strict_verify_ok_with_checksum(self, strict_repo):
        """مستودع verify_strict=True يحفظ checksum ويتحقق منه."""
        strict_repo.write_session("s1", _readings(10))
        assert strict_repo.verify_integrity("s1", strict=True) is True

    def test_strict_verify_detects_tampering(self, strict_repo, tmp_path):
        strict_repo.write_session("s1", _readings(10))
        # تعديل الملف بعد الكتابة
        path = tmp_path / "s1.parquet"
        with open(path, "ab") as f:
            f.write(b"tampered")
        assert strict_repo.verify_integrity("s1", strict=True) is False

    def test_verify_missing_session(self, repo):
        assert repo.verify_integrity("ghost") is False


# ─────────────────────────────────────────────
#  7. الحذف
# ─────────────────────────────────────────────

class TestDelete:
    def test_delete_removes_parquet_and_meta(self, repo, tmp_path):
        repo.write_session("s1", _readings(5))
        repo.delete_session("s1")
        assert not (tmp_path / "s1.parquet").exists()
        assert not (tmp_path / "s1.meta.json").exists()

    def test_delete_nonexistent_returns_true(self, repo):
        """الحذف يجب أن يكون آمناً حتى لو الجلسة غير موجودة."""
        assert repo.delete_session("ghost") is True

    def test_read_after_delete_raises(self, repo):
        repo.write_session("s1", _readings(5))
        repo.delete_session("s1")
        with pytest.raises(SessionNotFoundError):
            list(repo.read_session("s1"))


# ─────────────────────────────────────────────
#  8. Thread Safety
# ─────────────────────────────────────────────

class TestThreadSafety:
    def test_concurrent_writes_different_sessions(self, repo):
        """
        الكتابة المتزامنة على جلسات مختلفة يجب أن تنجح دون تلوث.
        """
        errors = []
        results = {}

        def write(sid: str, n: int):
            try:
                repo.write_session(sid, _readings(n, base_temp=float(n)))
                results[sid] = list(repo.read_session(sid))
            except Exception as e:
                errors.append((sid, str(e)))

        threads = [
            threading.Thread(target=write, args=(f"session_{i}", 200 + i * 10))
            for i in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors occurred: {errors}"
        for i in range(8):
            sid = f"session_{i}"
            assert len(results[sid]) == 200 + i * 10

    def test_concurrent_reads_same_session(self, repo):
        """القراءة المتزامنة لنفس الجلسة يجب أن تكون آمنة."""
        repo.write_session("shared", _readings(1_000))
        errors = []
        row_counts = []

        def read():
            try:
                rows = list(repo.read_session("shared"))
                row_counts.append(len(rows))
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert all(c == 1_000 for c in row_counts)


# ─────────────────────────────────────────────
#  9. اختبار السكربت (دمج اختياري)
# ─────────────────────────────────────────────

class TestMigrationScript:
    def test_migrate_dry_run(self, tmp_path):
        """dry-run لا يُنشئ أي ملفات."""
        import sys
        sys.path.insert(0, str(Path(__file__).parents[3]))
        from scripts.migrate_pickle_to_parquet import migrate

        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()

        # إنشاء ملف pickle وهمي
        import pickle, pandas as pd
        df = pd.DataFrame({"a": [1, 2, 3]})
        with open(source / "test.pkl", "wb") as f:
            pickle.dump(df, f)

        report = migrate(source, target, dry_run=True)
        assert len(report["skipped"]) == 1
        assert not (target / "test.parquet").exists()

    def test_migrate_actual(self, tmp_path):
        """هجرة فعلية تُنشئ ملفات صالحة."""
        from scripts.migrate_pickle_to_parquet import migrate
        import pickle, pandas as pd

        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()

        df = pd.DataFrame({"x": [10, 20, 30], "y": [1.1, 2.2, 3.3]})
        with open(source / "session_a.pkl", "wb") as f:
            pickle.dump(df, f)

        report = migrate(source, target)
        assert len(report["success"]) == 1
        assert len(report["failed"]) == 0
        assert (target / "session_a.parquet").exists()

        # التحقق من البيانات
        result = pd.read_parquet(target / "session_a.parquet")
        assert len(result) == 3
        assert list(result.columns) == ["x", "y"]