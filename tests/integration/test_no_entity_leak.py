import subprocess
import sys
import os


def test_guard_allows_no_leaks():
    """Run the guard script; it must exit 0 (no forbidden imports in protected paths)."""
    script = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'check_no_core_entity_imports.py')
    script = os.path.abspath(script)
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
    assert result.returncode == 0, "Guard detected entity imports in protected paths"
