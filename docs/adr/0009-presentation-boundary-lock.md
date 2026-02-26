# ADR-0009: Presentation Boundary Lock — Architectural Law

## Status
**APPROVED — ENFORCED**
*Violations block merge immediately. No exceptions.*

## Date
2026-02-04

## 1. Immutable Boundary Definition
The Presentation Layer is strictly defined as:

```text
src/presentation/
├── reporting/   # Data formatting only (CSV/PDF/HTML)
├── cli/         # Command-line interfaces (wiring only)
└── messages/    # Centralized MessageMap (single source of truth)
```

### 2. Forbidden Imports (Merge-Blocking)
Any file under `src/presentation/` MUST NOT contain:

```python
# ❌ ABSOLUTELY FORBIDDEN — blocks merge
from src.domain.entities import *
from src.domain.value_objects import *
from src.infrastructure import *
```

### 3. Message Drift Prevention
All user-facing text MUST flow through:

```python
from src.presentation.messages.message_map import MessageMap
MessageMap.get("DECISION_ACCEPTED")  # ✅ Only allowed pattern
```
Hardcoded Arabic/English text outside `message_map.py` = **merge blocked**.

### 4. Business Logic Ban
Presentation layer MUST contain:
*   ✅ Data formatting (CSV → PDF conversion)
*   ✅ Wiring (Composition Root invocation)
*   ❌ **NO business logic** (decision rules, calculations, validations)

## Enforcement Mechanism
*   **Guard Script**: `scripts/check_no_core_entity_imports.py` (already active)
*   **CI Enforcement**: `.github/workflows/guard.yml` blocks PRs violating this law
*   **Merge Block**: Any violation = automatic rejection (no human override)

## Verification
*   ✅ 88/88 tests passing
*   ✅ Zero entity leakage
*   ✅ MessageMap centralized
*   ✅ Legacy fully isolated

## Consequences of Violation
*   PR rejected automatically by CI
*   No "temporary exception" allowed
*   Architectural debt = immediate blocker (not technical debt)

## Immutable Status
This boundary is permanent. Future phases (CLI/API) MUST comply — not bypass.

## Signatures
**Architecture Team — 2026-02-04**
*This is not a guideline. This is architectural law.*