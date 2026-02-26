# Berlinger Fridge-tag® 2 E Format Specifications
## Source: debug_ft2.py + run_ft2_pipeline.py analysis

### Critical Patterns Observed
1. **Header Signature**
   - Must contain: `Device: Q-tag Fridge-tag 2 E` OR `Serial: 130600113438`
   - Detection: First 5 lines must contain "Fridge-tag" or "Berlinger"

2. **Hist Section Requirement**
   - Valid files MUST contain `Hist:` followed by at least one `Date:`
   - Files with `Hist:` but no `Date:` → always empty data → reject early

3. **Daily Entry Structure**
Date: YYYY-MM-DD
Min T: +X.X, TS Min T: HH:MM
Max T: +X.X, TS Max T: HH:MM
Avrg T: +X.X
- Extract only when all 4 fields present
- Skip entries with missing fields (fail-safe)

4. **Serial Field Format**
- Pattern: `Serial: 130600113438` (12-digit device ID)
- Extract via regex: `r'Serial:\s*(\d{12})'`

### Architectural Translation
→ Implement in `BerlingerFt2Reader` as pure parsing logic
→ NO business rules (decision logic belongs in Use Cases)
→ Return empty list on invalid format (fail-safe — not exception)
