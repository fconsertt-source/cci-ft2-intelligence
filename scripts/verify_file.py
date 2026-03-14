import sys
import argparse
from pathlib import Path
from src.shared.di_container import build_verify_and_record_uc
from src.domain.evidence.verification_result import VerificationStatus

def main():
    """
    CLI tool to verify a file and record the result in the forensic ledger.
    Usage: python -m scripts.verify_file <path_to_file>
    """
    parser = argparse.ArgumentParser(description="Verify a file and record result in forensic ledger.")
    parser.add_argument("file_path", type=Path, help="Path to the file to verify")
    args = parser.parse_args()

    if not args.file_path.exists():
        print(f"❌ Error: File not found: {args.file_path}")
        sys.exit(1)

    print(f"🔍 Verifying: {args.file_path} ...")
    
    try:
        # Bootstrap Use Case via DI Container
        use_case = build_verify_and_record_uc()
        result = use_case.execute(args.file_path)
        
        if result.status == VerificationStatus.SUCCESS:
            print("✅ SUCCESS: File is authentic.")
            print(f"   Diagnostics: {result.diagnostics}")
        else:
            print(f"❌ FAILED: {result.status.name}")
            print(f"   Diagnostics: {result.diagnostics}")
            
        print("📝 Result recorded in forensic ledger.")
        
    except Exception as e:
        print(f"💥 Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()