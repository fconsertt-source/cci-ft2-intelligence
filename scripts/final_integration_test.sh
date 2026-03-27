#!/bin/bash
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🧪 Final Integration Test                               ║"
echo "╚═══════════════════════════════════════════════════════════╝"

# 1. اختبارات LedgerEvent
echo ""
echo "📊 Testing LedgerEvent Taxonomy..."
python3 -c "
from src.domain.enums.ledger_event import LedgerEvent, EVENT_CATEGORY, EVENT_PRIORITY
print(f'✅ Events: {len(list(LedgerEvent))}')
print(f'✅ Categories: {len(set(EVENT_CATEGORY.values()))}')
print(f'✅ Priorities: {len(set(EVENT_PRIORITY.values()))}')
"

# 2. اختبار LanguageManager
echo ""
echo "🌐 Testing LanguageManager..."
python3 -c "
from src.shared.language_manager import LanguageManager
lang = LanguageManager()
lang.load_language('ar')
print(f'✅ AR: {lang.get(\"app.title\")}')
lang.load_language('en')
print(f'✅ EN: {lang.get(\"app.title\")}')
"

# 3. اختبار Ledger Writer
echo ""
echo "🔐 Testing Ledger Writer..."
python3 -c "
from src.infrastructure.adapters.ledger.ledger_writer_adapter import LedgerWriterAdapter
from src.domain.enums.ledger_event import LedgerEvent
from pathlib import Path
writer = LedgerWriterAdapter(Path('data/ledger/integration_test.jsonl'))
hash_val = writer.append(event_type=LedgerEvent.CYCLE_STARTED, operator='test')
print(f'✅ Entry created: {hash_val[:32]}...')
print(f'✅ Chain valid: {writer.verify_chain()}')
"

# 4. اختبارات pytest
echo ""
echo "🧪 Running pytest..."
pytest tests/unit/ tests/integration/ -q --tb=no 2>&1 | tail -5

echo ""
echo "✅ Integration Test Complete!"
