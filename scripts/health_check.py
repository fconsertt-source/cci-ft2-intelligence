#!/usr/bin/env python3
"""
Health Check Utility - فحص جاهزية النظام للعمل
"""
import sys
from pathlib import Path

def run_health_check():
    """Main health check function."""
    return check_system_health()

def check_all():
    """Alias for run_health_check."""
    return run_health_check()

def main():
    """Entry point."""
    if not check_system_health():
        sys.exit(1)
    sys.exit(0)

def check_system_health():
    print("🔍 Running System Health Check...")
    required_dirs = ["data/ledger", "data/input_ft2", "config", "logs"]
    
    for d in required_dirs:
        if not Path(d).exists():
            print(f"❌ Missing directory: {d}")
            return False
    
    # يمكن إضافة فحص للاتصال أو التراخيص هنا
    print("✅ System is healthy.")
    return True

if __name__ == "__main__":
    main()