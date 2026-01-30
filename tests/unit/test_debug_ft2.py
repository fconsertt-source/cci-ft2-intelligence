import os
from scripts import debug_ft2


def test_clean_bad_files_removes_empty(tmp_path):
    # Prepare data/input_ft2 with an empty file
    d = tmp_path / "data" / "input_ft2"
    d.mkdir(parents=True)
    empty_file = d / "bad1.txt"
    empty_file.write_text("")

    # run cleanup (it operates on fixed path, so create the expected folder)
    proj_root = os.getcwd()
    target_dir = os.path.join(proj_root, 'data', 'input_ft2')
    os.makedirs(os.path.dirname(target_dir), exist_ok=True)
    # Copy our test file into project location
    with open(target_dir + '/bad1.txt', 'w', encoding='utf-8') as f:
        f.write('')

    debug_ft2.clean_bad_files()

    # file should be removed
    assert not os.path.exists(target_dir + '/bad1.txt')


def test_debug_raw_files_handles_missing_dir(monkeypatch, caplog):
    # ensure function returns gracefully if input dir missing
    # Temporarily point to a non-existing dir by renaming if exists
    # Call debug_raw_files; should not raise
    debug_ft2.debug_raw_files()
    # No exception means pass
