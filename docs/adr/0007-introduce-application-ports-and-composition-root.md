# ADR 0007: Introduce Application Ports and Explicit Composition Root

Date: 2026-01-31

Status: Accepted

## Context

The codebase aims to follow Clean Architecture principles. While the direction was generally correct, dependency inversion was incomplete: Use Cases sometimes referenced implicit implementations and there were no formal application-level Ports (interfaces). This created a potential for coupling between Application and Infrastructure, and made it harder to evolve adapters without touching business orchestration.

Additionally, there is an existing "reader" path used by tests and some scripts that passes a concrete reader object directly into the Use Case.

## Decision

- Introduce explicit Application Ports to invert dependencies:
  - IDataRepository: reads DTOs for centers and vaccines.
  - IReporter: emits artifacts for a given AnalysisResultDTO.
- Keep the current `reader` constructor argument on `EvaluateColdChainSafetyUseCase` for backward compatibility in tests and scripts, but consider it a transitional mechanism.
- Establish an explicit Composition Root where Infrastructure adapters are wired to Use Cases. This is the only place that may import Infrastructure from Application.

## Added Ports

- src/application/ports/i_repository.py
  - IDataRepository.load_centers() -> Iterable[CenterDTO]
  - IDataRepository.load_vaccines() -> Iterable[VaccineDTO]
- src/application/ports/i_reporter.py
  - IReporter.generate(result: AnalysisResultDTO) -> None

These Ports use DTOs only; no domain entities or IO details.

## Transitional Legacy Reader

- EvaluateColdChainSafetyUseCase still supports `reader` and `repository` constructor params for existing tests and scripts.
- The `reader` path is maintained to avoid breaking changes during the transition. Over time, data ingestion should move behind IDataRepository (and future ports for readings), then the legacy `reader` can be deprecated.

## Composition Root

- A new explicit factory was added:
  - src/shared/di_container.py
    - build_evaluate_uc(): wires Ft2RepositoryAdapter (IDataRepository) and NoOpReporter (IReporter) into EvaluateColdChainSafetyUseCase.
- No conditional logic is present in the Composition Root; it only performs wiring.
- Application does not import Infrastructure anywhere else.

## Consequences

Positive:
- Proper dependency inversion enforced at the Application boundary.
- Swappable Infrastructure (e.g., CSV/FT2/SQL repository; PDF/CSV/ZIP reporters) without changes to Use Cases.
- Clear composition root that centralizes wiring and prevents accidental imports from Infrastructure into Application.
- Backward compatibility preserved for existing tests and scripts via the legacy `reader` signature.

Transition Costs:
- Temporary duplication of paths (Ports + legacy reader) until adapters fully cover data access.
- Minimal adapters created (Ft2RepositoryAdapter, NoOpReporter) to prove pluggability; more complete adapters will follow.
- Teams should prefer using build_evaluate_uc() going forward and progressively migrate away from directly constructing Use Cases with concrete readers.

## Notes

- After this ADR, it is safe to:
  - Unify `domain`/`core` naming (cosmetic cleanup), or
  - Add Skeleton Use Cases to complete ingest → validate → analyze → report flows, or
  - Introduce API/CLI layers, as they will compose strictly through the Composition Root.
