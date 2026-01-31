"""
Shim: simulate_vvm_scenarios was moved to tools/legacy.

When imported (e.g., by tests), this module proxies symbol imports to the
legacy implementation under `tools/legacy` so tests continue to work.
When executed as a script, it prints a notice and runs the legacy script.
"""

import sys
from pathlib import Path
import importlib.util

def _load_legacy_module():
    repo_root = Path(__file__).parent.parent
    legacy_path = repo_root / 'tools' / 'legacy' / 'simulate_vvm_scenarios.py'
    if not legacy_path.exists():
        return None

    spec = importlib.util.spec_from_file_location('legacy_simulate_vvm_scenarios', str(legacy_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Try to proxy symbols from the legacy tool so unit tests that import
# `scripts.simulate_vvm_scenarios` continue to work.
_legacy = _load_legacy_module()
if _legacy:
    simulate_scenario = getattr(_legacy, 'simulate_scenario')
    MockEntry = getattr(_legacy, 'MockEntry')
    main = getattr(_legacy, 'main', None)
else:
    simulate_scenario = None
    MockEntry = None
    main = None

if __name__ == '__main__':
    print("NOTICE: simulate_vvm_scenarios has been moved to tools/legacy/")
    print("Run: python3 tools/legacy/simulate_vvm_scenarios.py")
    if main:
        main()
    else:
        sys.exit(0)
