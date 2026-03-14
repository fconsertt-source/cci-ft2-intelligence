# tests/unit/shared/test_path_utils.py
"""Tests for shared.path_utils utilities."""



from src.shared import path_utils


def test_normalize_user_path_posix(tmp_path):
    p = tmp_path / "file.txt"
    p.write_text("x")
    result = path_utils.normalize_user_path(str(p))
    # on POSIX we expect the path to stay POSIX and exist
    assert result.exists()
    assert str(result).startswith(str(tmp_path))


def test_normalize_user_path_wsl():
    # simulate WSL path conversion
    out = path_utils.normalize_user_path("/mnt/c/Users/User/file.txt")
    # we may not run on Windows, but the returned string should include a drive letter
    assert "C:" in str(out) or "c:" in str(out)


def test_is_valid_ft2_path(tmp_path):
    f = tmp_path / "data.ft2.txt"
    f.write_text("x")
    assert path_utils.is_valid_ft2_path(f)
    assert not path_utils.is_valid_ft2_path(tmp_path / "nope.bin")


def test_get_safe_filename():
    # function replaces each illegal char individually so expect double underscore
    assert path_utils.get_safe_filename("a<>b|c") == "a__b_c"
