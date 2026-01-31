# CCI-FT2 Intelligence

## Engineering & Architecture Charter

**Document Type:** Architectural Governance Document
**Status:** Authoritative – Binding – Non‑Optional
**Applies To:** All code, configurations, tests, pipelines, and documentation

---

## 0. Purpose and Scope

This document defines the **architectural constitution** of the CCI‑FT2 Intelligence system.
It establishes immutable rules that govern design, implementation, extension, and maintenance.

Any technical decision, refactor, or feature **must comply** with this charter.

> Tooling convenience, delivery pressure, or developer preference **never override architecture**.

---

## 1. Architectural Model

CCI‑FT2 Intelligence follows a **Clean Architecture / Domain‑Driven Design (DDD)** hybrid model.

### Layer Model

1. **Domain** – Business rules, scientific models, invariants
2. **Application** – Use cases, orchestration, DTOs
3. **Infrastructure** – IO, parsing, persistence, reporting engines
4. **Interfaces** – CLI, API, visualization, external adapters

Dependencies flow **inward only**.

---

## 2. Strict Layer Separation

### Rule

No layer may bypass another or access internal details of an inner layer.

### Constraints

* Domain:

  * No dependency on frameworks, filesystems, databases, clocks, or external services
* Infrastructure / Interfaces:

  * Must not contain business rules or scientific logic

### Enforcement

* Communication occurs **only via interfaces and contracts** defined inward

### Objective

Maintain a portable, testable, framework‑agnostic core.

---

## 3. Domain Sovereignty (Entities vs DTOs)

### Rule

Domain entities are **internal assets** and never leave the Domain boundary.

### Constraints

* External communication uses **DTOs only**
* Explicit mapping is mandatory

### Prohibited

* Passing entities to:

  * Report generators
  * APIs
  * Parsers
  * Visualization modules

### Objective

Prevent coupling, lifecycle corruption, and data leakage.

---

## 4. Error and Exception Model

### Rule

Use Cases **declare failure**; they do not interpret or handle it.

### Constraints

* No ad‑hoc try/except blocks inside use cases
* Error handling is centralized

### Exception Taxonomy

* `DomainException`
* `ValidationException`
* `NotFoundException`
* `InfrastructureException`

### Objective

Deterministic failure paths and debuggable execution.

---

## 5. Test Discipline (Test‑First Mindset)

### Rule

Business logic must be validated **before** integration.

### Constraints

* Every use case must include:

  * Success‑path tests
  * Failure‑path tests
* Domain tests must not rely on:

  * IO
  * Time
  * Filesystem
  * External services

### Objective

Early regression detection and architectural confidence.

---

## 6. Dependency Injection Governance

### Rule

Dependency wiring is centralized and intentional.

### Constraints

* Each layer registers its own dependencies
* Composition Root orchestrates wiring only

### Prohibited

* Hidden instantiation inside use cases or entities

### Objective

Prevent configuration sprawl and implicit coupling.

---

## 7. Structural Traceability

### Rule

Architecture changes require architecture visibility.

### Constraints

* Any structural change requires:

  * Updated project tree snapshot
  * Updated project state manifest

### Objective

Preserve long‑term architectural memory.

---

## 8. Internal Language Policy

### Rule

Internal system language is **English only**.

### Constraints

* No localized or human‑facing messages inside:

  * Domain
  * Application

### Exception

Localization is permitted only in Interface layers.

### Objective

Avoid ambiguity, encoding issues, and test instability.

---

## 9. Architectural Decision Recording (ADR)

### Rule

Architectural decisions must be documented.

### Constraints

Any decision impacting:

* Structure
* Models
* Data flow
* Algorithms

requires an ADR entry.

### Objective

Prevent architectural amnesia and repetitive redesign cycles.

---

## 10. Authority and Precedence

In case of conflict:

1. Engineering Charter
2. ADRs
3. Decision Matrix
4. Release Notes
5. Implementation Documents

The **Charter always prevails**.

---

## 11. Final Statement

This charter is not guidance.

It is a **contract**.

Any contribution that violates it is considered **architecturally invalid**, regardless of functional correctness.

---

## Project State & ADR Adoption

To improve structural visibility and preserve traceability, the project adopts a formal Project State document and an ADR directory. See:

- `docs/ProjectState.md` — current canonical project structure and mapping to the Layer Model.
- `docs/adr/` — Architectural Decision Records. New structural or model decisions must have an ADR.

This change is recorded in `docs/adr/0001-adopt-structure.md` and becomes effective immediately. The Charter remains the authoritative source; ADRs provide recorded decisions that adhere to it.
