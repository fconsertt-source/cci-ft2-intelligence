"""Reporting package - thin initializer to make submodules importable during tests.

This package file ensures `src.reporting` is a regular package so that
submodules like `src.reporting.unified_pdf_generator` and
`src.reporting.pdf_generator` can be imported and patched in tests.
"""

__all__ = [
    "csv_reporter",
    "unified_pdf_generator",
    "pdf_generator",
]
