#!/bin/bash
# scripts/production_status_check.sh
# =================================
# Production Status Check - CCI-FT2-Intelligence
# =================================

# تأكد من وجود مجلد reports/
mkdir -p reports

# اسم الملف مع طابع زمني
REPORT_FILE="reports/production_status_check_$(date +%Y%m%d_%H%M%S).txt"

# دالة طباعة إلى stdout وأيضاً إلى التقرير
log() {
    echo -e "$1" | tee -a "$REPORT_FILE"
}

log "╔═══════════════════════════════════════════════════════════╗"
log "║   🛡️  CCI-FT2-Intelligence - Production Status Check      ║"
log "╚═══════════════════════════════════════════════════════════╝"
log ""

# ------------------------------------------------------------------
# 1. GIT STATUS
# ------------------------------------------------------------------
log "📍 GIT STATUS"
log "───────────────────────────────────────────────────────────"
git log -1 --oneline | tee -a "$REPORT_FILE"
git describe --tags 2>/dev/null | tee -a "$REPORT_FILE" || log "⚠️  No tags found"
log ""

# ------------------------------------------------------------------
# 2. TEST STATUS
# ------------------------------------------------------------------
log "🧪 TEST STATUS"
log "───────────────────────────────────────────────────────────"
pytest tests/unit/ tests/integration/ -q --disable-warnings --maxfail=0 --tb=short 2>&1 | tee -a "$REPORT_FILE" | tail -10
log ""

# ------------------------------------------------------------------
# 3. CRITICAL FILES CHECK
# ------------------------------------------------------------------
log "📁 CRITICAL FILES CHECK"
log "───────────────────────────────────────────────────────────"

if grep -q "from src.application.security.license_guard import LicenseGuard" src/shared/di_container.py 2>/dev/null; then
    log "✅ LicenseGuard path: CORRECT (application.security)"
else
    log "❌ LicenseGuard path: WRONG (should be application.security)"
fi

if grep -q "from unittest.mock import Mock" src/shared/di_container.py 2>/dev/null; then
    log "⚠️  DI Container: Contains Mocks (should be production-only)"
else
    log "✅ DI Container: Clean (no Mocks)"
fi

if [ -f "src/infrastructure/security/hybrid_evidence_validator.py" ]; then
    log "✅ HybridEvidenceValidator: EXISTS"
else
    log "❌ HybridEvidenceValidator: MISSING"
fi

if [ -f "data/ledger/verification_ledger.jsonl" ]; then
    LEDGER_ENTRIES=$(wc -l < data/ledger/verification_ledger.jsonl)
    log "✅ Ledger: EXISTS ($LEDGER_ENTRIES entries)"
else
    log "❌ Ledger: MISSING"
fi
log ""

# ------------------------------------------------------------------
# 4. DEPENDENCIES CHECK
# ------------------------------------------------------------------
log "📦 DEPENDENCIES CHECK"
log "───────────────────────────────────────────────────────────"
python -c "import filelock; print('✅ filelock: installed')" 2>/dev/null | tee -a "$REPORT_FILE" || log "❌ filelock: MISSING"
python -c "import fitz; print('✅ PyMuPDF: installed')" 2>/dev/null | tee -a "$REPORT_FILE" || log "❌ PyMuPDF: MISSING"
python -c "from cryptography.hazmat.primitives.asymmetric import ec; print('✅ cryptography: installed')" 2>/dev/null | tee -a "$REPORT_FILE" || log "❌ cryptography: MISSING"
log ""

# ------------------------------------------------------------------
# 5. ARCHITECTURE GUARDS
# ------------------------------------------------------------------
log "🛡️  ARCHITECTURE GUARDS"
log "───────────────────────────────────────────────────────────"
for script in check_no_core_entity_imports check_di_container_usage check_src_root_clean check_layer_dependencies; do
    if [ -f "scripts/${script}.py" ]; then
        python -m scripts.${script} 2>&1 | tee -a "$REPORT_FILE" | grep -E "OK|FAIL" || log "⚠️  ${script}: Unexpected output"
    else
        log "⚠️  ${script}: Script not found"
    fi
done
log ""

# ------------------------------------------------------------------
# 6. LEDGER INTEGRITY
# ------------------------------------------------------------------
log "🔐 LEDGER INTEGRITY"
log "───────────────────────────────────────────────────────────"
if [ -f "scripts/audit_ledger.py" ]; then
    python scripts/audit_ledger.py 2>&1 | tee -a "$REPORT_FILE" | grep -E "VERIFIED|FAILED|Entries" || log "⚠️  Ledger audit: Unexpected output"
else
    log "⚠️  Ledger audit script not found"
fi
log ""

# ------------------------------------------------------------------
# 7. FINAL SUMMARY
# ------------------------------------------------------------------
log "╔═══════════════════════════════════════════════════════════╗"
log "║                    📊 FINAL SUMMARY                       ║"
log "╚═══════════════════════════════════════════════════════════╝"
log ""
log "📍 Git commit:"
git log -1 --oneline | tee -a "$REPORT_FILE"
log ""
log "📍 Latest tag:"
git describe --tags 2>/dev/null | tee -a "$REPORT_FILE" || log "⚠️  No tags found"
log ""
log "📍 Ledger entries:"
if [ -f "data/ledger/verification_ledger.jsonl" ]; then
    log "  $(wc -l < data/ledger/verification_ledger.jsonl) entries"
else
    log "  Ledger file missing"
fi
log ""
log "📍 Report saved to $REPORT_FILE"
log ""
log "═══════════════════════════════════════════════════════════"