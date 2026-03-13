import os
import pytest
import hashlib
from src.infrastructure.adapters.filesystem_adapter import SafeFileOperations

@pytest.fixture
def file_ops():
    return SafeFileOperations()

@pytest.fixture
def test_files(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()

    file1 = src_dir / "file1.txt"
    file1.write_text("This is a test file.")
    
    return src_dir, dst_dir, file1

def test_compute_hash(file_ops, test_files):
    _, _, file1 = test_files
    
    # Calculate expected hash
    h = hashlib.sha256()
    h.update(file1.read_bytes())
    expected_hash = h.hexdigest()

    # Test
    actual_hash = file_ops.compute_hash(file1)
    
    assert actual_hash == expected_hash

def test_get_size(file_ops, test_files):
    _, _, file1 = test_files
    expected_size = os.path.getsize(file1)
    
    actual_size = file_ops.get_size(file1)
    
    assert actual_size == expected_size

def test_atomic_move(file_ops, test_files):
    src_dir, dst_dir, src_file = test_files
    
    dst_file = dst_dir / src_file.name
    
    src_hash = file_ops.compute_hash(src_file)
    src_size = file_ops.get_size(src_file)

    # The move
    file_ops.atomic_move(src_file, dst_file)

    # Assertions
    assert not src_file.exists()
    assert dst_file.exists()
    
    dst_hash = file_ops.compute_hash(dst_file)
    dst_size = file_ops.get_size(dst_file)

    assert dst_hash == src_hash
    assert dst_size == src_size

def test_atomic_move_raises_error(file_ops, test_files, monkeypatch):
    src_dir, dst_dir, src_file = test_files
    dst_file = dst_dir / src_file.name

    # Mock os.replace to fail using built-in monkeypatch
    monkeypatch.setattr('os.replace', lambda src, dst: (_ for _ in ()).throw(OSError("Mocked error")))

    with pytest.raises(RuntimeError, match="Atomic move failed: Mocked error"):
        file_ops.atomic_move(src_file, dst_file)
    
    # Assert that tmp file is cleaned up
    tmp_file = dst_file.with_suffix('.tmp')
    assert not tmp_file.exists()
    # Assert source file still exists
    assert src_file.exists()
