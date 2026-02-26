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
    
    # When: I generate device report
    report = device_use_case.execute(device_id=device_id)
    
    # Then: final status should be "SAFE"
    assert report.final_status == "SAFE"
    
    # And: all excursions should be "SAFE"
    for excursion in report.excursions:
        assert excursion.impact_level == "SAFE"
    
    # And: total records match input count
    assert report.total_records == 2  # ← عدد السجلات في fixture
    assert len(report.excursions) == 2  # ← نفس العدد
