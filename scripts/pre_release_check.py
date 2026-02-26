#!/usr/bin/env python3
"""
Pre-release check script for CCI-FT2-Intelligence

This script runs all essential checks before allowing the system
to go into production/trial. It ensures:

1. Clean architecture rules are respected.
2. All unit, integration, and BDD tests pass.
3. DI container usage is correct.
4. Archive and core entities are clean.
5. Layer dependencies are correct.
6. System health is verified.
7. Results are logged to Ledger for audit trail.

Usage:
    python pre_release_check.py
    python pre_release_check.py --quick
    python pre_release_check.py --skip-tests
    python pre_release_check.py --ledger-log

Trial Period: 90 days starting 2026-02-25
"""

import subprocess
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

DEFAULT_TIMEOUT = 300  # 5 minutes per check
REPORT_DIR = Path("reports")
REPORT_PATH = REPORT_DIR / "pre_release_report.json"

# ═══════════════════════════════════════════════════════════════
# Check Definitions
# ═══════════════════════════════════════════════════════════════

CRITICAL_CHECKS = [
    {
        "description": "Check for no direct imports from core entities",
        "cmd": ["python", "scripts/check_no_core_entity_imports.py"],
        "category": "architecture"
    },
    {
        "description": "Check DI container usage",
        "cmd": ["python", "scripts/check_di_container_usage.py"],
        "category": "architecture"
    },
    {
        "description": "Check layer dependencies",
        "cmd": ["python", "scripts/check_layer_dependencies.py"],
        "category": "architecture"
    },
    {
        "description": "Check Ledger integrity",
        "cmd": ["python", "-m", "scripts.audit_ledger"],
        "category": "system"
    },
    {
        "description": "Verify archive structure",
        "cmd": ["python", "-m", "scripts.verify_lifecycle"],
        "category": "system"
    },
]

FULL_CHECKS = CRITICAL_CHECKS + [
    {
        "description": "Check src root clean",
        "cmd": ["python", "scripts/check_src_root_clean.py"],
        "category": "architecture"
    },
    {
        "description": "Run all unit and integration tests",
        "cmd": ["pytest", "-q", "--tb=short"],
        "category": "tests"
    },
    {
        "description": "Run BDD tests",
        "cmd": ["pytest", "tests/bdd/", "-v"],
        "category": "tests"
    },
    {
        "description": "Check Python dependencies",
        "cmd": ["pip", "check"],
        "category": "dependencies"
    },
    {
        "description": "Check disk space (min 10GB free)",
        "cmd": ["python", "scripts/check_disk_space.py", "--min-gb", "10"],
        "category": "system"
    },
]

# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════

def run_command(cmd: List[str], description: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[bool, str, str]:
    """
    Run a command and capture result.
    
    Returns:
        Tuple[bool, str, str]: (passed, stdout, stderr)
    """
    print(f"\n🔹 Running: {description}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"  Timeout: {timeout}s")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
            timeout=timeout
        )
        print(f"✅ {description} PASSED")
        return True, result.stdout, None
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} FAILED")
        print(f"  Exit Code: {e.returncode}")
        if e.stderr:
            print(f"  Stderr: {e.stderr[:500]}...")
        return False, e.stdout, e.stderr
        
    except subprocess.TimeoutExpired as e:
        print(f"❌ {description} TIMEOUT ({timeout}s)")
        return False, None, "Timeout expired"
        
    except FileNotFoundError:
        print(f"❌ {description} FAILED - Command not found")
        return False, None, "Command not found"


def generate_report(results: List[Dict], output_path: Path, ledger_log: bool = False) -> Dict:
    """
    Generate JSON report for archival.
    
    Optionally logs to Ledger for forensic audit trail.
    """
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_checks": total,
        "passed": passed,
        "failed": failed,
        "success_rate": round((passed / total) * 100, 2) if total > 0 else 0,
        "status": "READY" if failed == 0 else "BLOCKED",
        "checks": results,
        "trial_period": {
            "start_date": "2026-02-25",
            "end_date": "2026-05-26",
            "duration_days": 90
        }
    }
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 Report saved: {output_path}")
    
    # Log to Ledger if requested
    if ledger_log and failed == 0:
        try:
            from src.shared.di_container import container
            from src.application.ports.ledger_writer_port import LedgerWriterPort
            from src.domain.ledger.events import LedgerEvent
            
            ledger = container.resolve(LedgerWriterPort)
            ledger.append(
                event_type=LedgerEvent.LEDGER_INTEGRITY_CHECK,
                file_hash="PRE_RELEASE_CHECK",
                event_id=f"prerelease-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                ft2_serial="SYSTEM",
                authenticity_status=report["status"]
            )
            print("✅ Results logged to Ledger for audit trail")
        except Exception as e:
            print(f"⚠️  Failed to log to Ledger: {e}")
    
    return report


def print_summary(results: List[Dict]) -> None:
    """Print formatted summary"""
    print("\n" + "="*60)
    print("📊 PRE-RELEASE CHECK SUMMARY")
    print("="*60)
    
    by_category = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"passed": 0, "failed": 0}
        if r["passed"]:
            by_category[cat]["passed"] += 1
        else:
            by_category[cat]["failed"] += 1
    
    for cat, stats in sorted(by_category.items()):
        total = stats["passed"] + stats["failed"]
        print(f"\n{cat.upper()}:")
        print(f"  ✅ Passed: {stats['passed']}/{total}")
        if stats["failed"] > 0:
            print(f"  ❌ Failed: {stats['failed']}/{total}")
    
    total_passed = sum(1 for r in results if r["passed"])
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_passed}/{len(results)} checks passed")
    print(f"{'='*60}")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Pre-Release Check for CCI-FT2-Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python pre_release_check.py
    python pre_release_check.py --quick
    python pre_release_check.py --skip-tests
    python pre_release_check.py --ledger-log
        """
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip pytest (for quick architecture checks)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only critical checks"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPORT_PATH,
        help=f"Path for JSON report output (default: {REPORT_PATH})"
    )
    parser.add_argument(
        "--ledger-log",
        action="store_true",
        help="Log results to Ledger for audit trail"
    )
    
    args = parser.parse_args()
    
    # Select checks based on flags
    if args.quick:
        checks = CRITICAL_CHECKS
    elif args.skip_tests:
        checks = [c for c in FULL_CHECKS if c["category"] != "tests"]
    else:
        checks = FULL_CHECKS
    
    print("\n" + "="*60)
    print("🛡️  CCI-FT2-INTELLIGENCE - PRE-RELEASE CHECK")
    print("="*60)
    print(f"📅 Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"📋 Total Checks: {len(checks)}")
    print(f"📝 Report: {args.report}")
    if args.quick:
        print("⚡ Mode: QUICK (critical checks only)")
    elif args.skip_tests:
        print("⚡ Mode: NO TESTS (architecture + system only)")
    print("="*60)
    
    # Run checks
    results = []
    for check in checks:
        passed, stdout, stderr = run_command(check["cmd"], check["description"])
        results.append({
            "description": check["description"],
            "category": check.get("category", "unknown"),
            "passed": passed,
            "command": " ".join(check["cmd"]),
            "stdout": stdout[:1000] if stdout else None,  # Limit for report
            "stderr": stderr[:1000] if stderr else None
        })
    
    # Generate report
    generate_report(results, args.report, args.ledger_log)
    
    # Print summary
    print_summary(results)
    
    # Final verdict
    all_passed = all(r["passed"] for r in results)
    print("\n" + "="*60)
    if all_passed:
        print("🎯 ALL CHECKS PASSED")
        print("✅ System is READY for trial deployment!")
        print("📅 Trial Period: 90 days (2026-02-25 to 2026-05-26)")
        sys.exit(0)
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("❌ Fix issues before trial deployment.")
        failed_checks = [r["description"] for r in results if not r["passed"]]
        print("\nFailed checks:")
        for fc in failed_checks:
            print(f"  - {fc}")
        sys.exit(1)


if __name__ == "__main__":
    main()