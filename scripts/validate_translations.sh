#!/bin/bash
# scripts/validate_translations.sh

echo "🔍 Validating translation files..."

# Check JSON validity
python3 -c "
import json
import sys

def validate_file(path, lang):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f'✅ {lang}: Valid JSON ({len(data)} keys)')
        return data
    except Exception as e:
        print(f'❌ {lang}: Invalid - {e}')
        return None

en = validate_file('translations/en/messages.json', 'English')
ar = validate_file('translations/ar/messages.json', 'Arabic')

if en and ar:
    # Check for missing keys
    en_keys = set(en.keys())
    ar_keys = set(ar.keys())
    missing = en_keys - ar_keys

    if missing:
        print(f'⚠️  Arabic missing {len(missing)} keys:')
        for key in sorted(list(missing)[:10]):
            print(f'   - {key}')
        if len(missing) > 10:
            print(f'   ... and {len(missing) - 10} more')
    else:
        print('✅ All keys present in both languages')

    # Check for variable consistency
    import re
    var_pattern = r'\{(\w+)\}'

    for key in en_keys & ar_keys:
        en_vars = set(re.findall(var_pattern, en[key]))
        ar_vars = set(re.findall(var_pattern, ar[key]))
        if en_vars != ar_vars:
            print(f'⚠️  Variable mismatch in \"{key}\": EN={en_vars}, AR={ar_vars}')

    print('✅ Validation complete')
"
