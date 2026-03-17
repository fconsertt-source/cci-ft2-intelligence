"""
اختبارات وحدة لـ FilesystemAdapter
"""

import hashlib

import pytest

from src.infrastructure.adapters.filesystem_adapter import FilesystemAdapter


@pytest.fixture
def adapter():
    """تهيئة adapter للاختبار"""
    return FilesystemAdapter()


@pytest.fixture
def temp_file(tmp_path):
    """إنشاء ملف مؤقت للاختبار"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test content")
    return file_path


class TestFilesystemAdapter:
    """اختبارات FilesystemAdapter"""

    def test_compute_hash(self, adapter, temp_file):
        """يجب حساب hash صحيح"""
        expected = hashlib.sha256(b"test content").hexdigest()
        actual = adapter.compute_hash(temp_file)

        assert actual == expected

    def test_exists_true(self, adapter, temp_file):
        """يجب إرجاع True للملف الموجود"""
        assert adapter.exists(temp_file) is True

    def test_exists_false(self, adapter, tmp_path):
        """يجب إرجاع False للملف غير الموجود"""
        non_existent = tmp_path / "nonexistent.txt"
        assert adapter.exists(non_existent) is False

    def test_get_size(self, adapter, temp_file):
        """يجب إرجاع الحجم الصحيح"""
        assert adapter.get_size(temp_file) == 12  # "test content" = 12 bytes

    def test_move_atomic(self, adapter, tmp_path):
        """يجب نقل الملف بشكل ذري"""
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"

        src.write_text("test content")

        adapter.move_atomic(src, dst)

        assert adapter.exists(dst) is True
        assert adapter.exists(src) is False
        assert dst.read_text() == "test content"

    def test_delete_secure(self, adapter, tmp_path):
        """يجب حذف الملف بشكل آمن"""
        file_path = tmp_path / "to_delete.txt"
        file_path.write_text("sensitive data")

        adapter.delete_secure(file_path)

        assert adapter.exists(file_path) is False
