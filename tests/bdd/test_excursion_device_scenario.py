# tests/bdd/test_excursion_device_scenario.py
#!/usr/bin/env python3
"""
BDD: Excursion device scenario
✔ متوافق مع منطق UseCase الحالي
✔ فقط السجلات غير الآمنة تُسجَّل كـ excursions
"""

from src.application.use_cases.requests import GenerateDeviceReportRequest


def test_device_with_single_heat_excursion(excursion_use_case):
    """
    Scenario: Device with one heat excursion
        Given device "130600112764" with one safe reading and one high-temperature reading
        When I generate device report
        Then final status should be "PARTIAL"
        And exactly one excursion should be recorded
        And the excursion should reflect the max temperature
    """
    device_id = "130600112764"
    request = GenerateDeviceReportRequest(device_id=device_id)

    report = excursion_use_case.execute(request)

    assert report.device_id == "130600112764"
    assert report.vaccine_type == "Hepatitis_B"
    assert report.final_status == "PARTIAL", f"Expected PARTIAL, got: {report.final_status}"
    assert report.total_records == 2, f"Expected 2 records, got: {report.total_records}"
    assert len(report.excursions) == 1, f"Expected 1 excursion, got: {len(report.excursions)}"

    excursion = report.excursions[0]
    assert excursion.impact_level == "PARTIAL", f"Expected PARTIAL excursion, got: {excursion.impact_level}"
    assert excursion.max_temperature == 9.0, f"Expected max temperature 9.0, got: {excursion.max_temperature}"
