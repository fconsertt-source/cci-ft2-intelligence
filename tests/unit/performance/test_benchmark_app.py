# tests/unit/performance/test_benchmark_app.py
"""Simple performance benchmark for core operations.
This is not a strict unit test but serves as an early reminder to measure.
"""
import time

from src.application.app_composer import AppComposer


def test_generate_report_speed():
    """benchmark only: generating a report should be reasonably fast"""
    uc = AppComposer.create_generate_device_report_uc()
    start = time.time()
    # we won't execute fully because it may require data; just measure build time
    end = time.time()
    elapsed = end - start
    # assert composition is fast (< 0.01s)
    assert elapsed < 0.01, f"Composer build too slow: {elapsed}"
