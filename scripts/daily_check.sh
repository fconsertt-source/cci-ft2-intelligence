#!/bin/bash
# مراقبة يومية للإنتاج

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🛡️  Daily Production Check - $(date +%Y-%m-%d)          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Tests: $(pytest -q --tb=no 2>&1 | tail -1)"
echo "🔐 Ledger: $(wc -l < data/ledger/verification_ledger.jsonl 2>/dev/null || echo 0) entries"
echo "💾 Disk: $(df -h /home | tail -1 | awk '{print $5}')"
echo ""
python -m scripts.audit_ledger 2>&1 | grep -E "VERIFIED|FAILED" || echo "Audit pending"
echo ""
echo "═══════════════════════════════════════════════════════════"
