from scripts.simulate_vvm_scenarios import simulate_scenario, MockEntry


def test_simulate_scenario_runs_without_error(capfd):
    entries = [
        MockEntry(5.0, 60),
        MockEntry(15.0, 24 * 60),
    ]
    simulate_scenario("Test Scenario", entries)
    captured = capfd.readouterr()
    assert "Test Scenario" in captured.out
