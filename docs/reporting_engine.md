# Reporting Engine Upgrade (v2.0)

This document describes the new PDF generation engine being developed under the
`feature/pdf-engine-upgrade` branch. It will replace the legacy
`UnifiedPDFGenerator` with a modular, testable, and Arabic-aware implementation.

## Getting Started

1. Build container: `docker build -t cci-ft2-reporting .`
2. Run tests inside container: `docker run --rm -v "$PWD":/app cci-ft2-reporting pytest tests/golden -q`

> **Arabic support:** place an Arabic-capable TTF file (e.g. `Tajawal-Regular.ttf`) under
> `assets/fonts` or configure `paths.fonts_dir` in `config.yaml` before running the
> generator. Without a custom font the engine falls back to Helvetica and Arabic
> glyphs may not render.

## Module Structure

- `src/presentation/reporting/components/` – header, table, charts, arabic
  processor builders.
- `src/infrastructure/adapters/reporting/new_pdf_engine.py` – high level
  generator.
- `src/infrastructure/adapters/reporting/pdf_strategy.py` – updated strategies
  pointing to new engine.

Further details and design diagrams will be added during Phase 2.
