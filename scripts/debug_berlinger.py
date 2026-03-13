# scripts/debug_berlinger.py
#!/usr/bin/env python3
"""تشخيص تشغيل Berlinger Verifier في البيئة الحالية"""

import subprocess
from pathlib import Path

def diagnose(jar_path: Path, sample_file: Path):
    print(f"🔍 Java version:")
    subprocess.run(["java", "-version"], stderr=subprocess.STDOUT)
    
    print(f"\n🔍 Testing headless mode:")
    cmd = [
        "java",
        "-Djava.awt.headless=true",
        "-Dfile.encoding=UTF-8",
        "-Duser.language=en",
        "-jar", str(jar_path), str(sample_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    print(f"Return code: {result.returncode}")
    print(f"Stdout (first 300 chars):\n{result.stdout[:300]}")
    print(f"Stderr (first 300 chars):\n{result.stderr[:300]}")
    
    # تصنيف النتيجة
    output = (result.stdout + result.stderr).lower()
    if "headlessexception" in output:
        print("\n⚠️  Result: GUI_REQUIRED - verifier needs display")
    elif result.returncode == 0 and ("valid" in output or "✓" in output):
        print("\n✅ Result: Works in headless mode")
    elif result.returncode != 0:
        print(f"\n❌ Result: Failed with code {result.returncode}")
    else:
        print("\n❓ Result: Unclear - needs manual review")

if __name__ == "__main__":
    jar = Path("assets/verifiers/berlinger/verifier-3.5-basic-with-dependencies.jar")
    sample = Path("tests/fixtures/ft2/txt/130600113438_202407221216.txt")
    diagnose(jar, sample)