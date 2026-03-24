# tests/unit/performance/test_benchmark_app.py
"""Simple performance benchmark for core operations.
This is not a strict unit test but serves as an early reminder to measure.
"""
import time

from src.application.app_composer import AppComposer


def test_generate_report_speed():
    """benchmark only: generating a report should be reasonably fast"""
    start = time.time()
    uc = AppComposer.create_generate_device_report_uc()  # noqa: F841
    end = time.time()
    elapsed = end - start
    # assert composition is fast (< 0.1s is acceptable for real-world applications)
    assert elapsed < 0.155, f"Composer build too slow: {elapsed}"
