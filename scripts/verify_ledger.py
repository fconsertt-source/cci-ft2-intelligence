import sys
from src.shared.di_container import build_ledger_writer

def main():
    """
    CLI tool to verify the integrity of the forensic ledger hash chain.
    Usage: python -m scripts.verify_ledger
    """
    print("🔍 Verifying Forensic Ledger Integrity...")
    
    try:
        # Bootstrap Ledger Writer via DI Container
        ledger = build_ledger_writer()
        
        # Perform Integrity Check
        is_valid, error = ledger.verify_integrity()
        
        if is_valid:
            state = ledger.get_chain_state()
            print("✅ LEDGER INTEGRITY VERIFIED")
            print(f"   Entries: {state.entry_count}")
            print(f"   Last Hash: {state.last_entry_hash}")
        else:
            print("❌ LEDGER TAMPERING DETECTED")
            print(f"   Error: {error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()