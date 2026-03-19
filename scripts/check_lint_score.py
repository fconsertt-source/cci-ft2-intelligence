#!/usr/bin/env python3
"""
Quality Gate for CCI-FT2 Intelligence
Prevents commits that lower code quality below 8.5/10
Version: 1.1
"""

import re
import subprocess
import sys
from pathlib import Path

MIN_SCORE = 8.5


def run_pylint():
    """Run pylint analysis with optimized settings."""
    result = subprocess.run(
        ["pylint", "src", "--rcfile=.pylintrc"], capture_output=True, text=True
    )
    # Pylint returns 0 for perfect score, 32 for warnings, etc.
    return result.stdout if result.stdout else result.stderr


def extract_score(text):
    """Extract pylint score from output."""
    match = re.search(r"rated at ([0-9.]+)/10", text)
    return float(match.group(1)) if match else None


def main():
    """Main quality gate logic."""
    report_path = Path("reports/pylint/final.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    text = run_pylint()
    report_path.write_text(text)

    score = extract_score(text)

    if score is None:
        print("❌ Could not determine Pylint score")
        print("   Run manually: pylint src --rcfile=.pylintrc")
        return 1

    if score < MIN_SCORE:
        print(f"❌ Quality gate FAILED: {score}/10 (minimum: {MIN_SCORE})")
        print("   Fix issues and retry commit")
        return 1

    print(f"✅ Quality gate PASSED: {score}/10")
    return 0


if __name__ == "__main__":
    sys.exit(main())
