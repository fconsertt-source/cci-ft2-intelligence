import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_license_gen_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch HOME to tmpdir
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = tmpdir

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/license-gen.py",
                    "--install",
                    "--expiry",
                    "1",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            license_dir = Path(tmpdir) / ".cci_ft2"
            assert license_dir.exists()
            assert (license_dir / "license.dat").exists()
            assert (license_dir / "public.pem").exists()

        finally:
            if old_home:
                os.environ["HOME"] = old_home
