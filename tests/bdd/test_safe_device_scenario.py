# tests/bdd/test_safe_device_scenario.py
#!/usr/bin/env python3
"""
BDD: Safe device scenario
✔ متوافق مع UseCase الحالي
✔ يستخدم GenerateDeviceReportRequest
"""

import pytest

from src.application.use_cases.generate_device_report_uc import (
    GenerateDeviceReportRequest,
)


def test_safe_device_with_normal_temperatures(device_use_case):
    """
    Scenario: Safe device with normal temperatures
        Given device "130600112764" with normal thermal history
        When I generate device report
        Then final status should be "SAFE"
        And all excursions should be "SAFE"
        And total records match input count
    """
    # Given: device with normal thermal history
    device_id = "130600112764"

    # ✅ إنشاء Request Object بدلاً من تمرير device_id مباشرة
    request = GenerateDeviceReportRequest(device_id=device_id)

    # When: I generate device report
    report = device_use_case.execute(request)

    # Then: final status should be "SAFE"
    assert (
        report.final_status == "SAFE"
    ), f"Expected SAFE status, got: {report.final_status}"

    # And: all excursions should be "SAFE"
    for excursion in report.excursions:
        assert (
            excursion.impact_level == "SAFE"
        ), f"Expected SAFE excursion, got: {excursion.impact_level}"

    # And: total records match input count
    assert report.total_records == 2, f"Expected 2 records, got: {report.total_records}"
    assert (
        len(report.excursions) == 2
    ), f"Expected 2 excursions, got: {len(report.excursions)}"
