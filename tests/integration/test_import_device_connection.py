from src.infrastructure.adapters.json_device_repository import \
    JsonDeviceRepository


def test_device_repository_constructs_complete_entities(tmp_path):
    """
    Verify ThermalRecord carries device_id as intrinsic identity.
    This is a Domain Model integrity test — not an infrastructure test.
    """
    output_file = tmp_path / "imported_data.json"
    imported_format_data = [
        {
            "id": "130600112764_20211201000000",
            "device_id": "130600112764",
            "timestamp": "2021-12-01 00:00:00",
            "temperature": 4.5,
            "vaccine_type": "Hepatitis_B",
            "duration_minutes": 1440.0,
            "vvm_stage": "VVM_STAGE_1",
        }
    ]

    with open(output_file, "w", encoding="utf-8") as f:
        import json

        json.dump(imported_format_data, f)

    repo = JsonDeviceRepository(json_path=output_file)
    history = repo.get_device_history("130600112764")

    assert len(history) == 1
    assert history[0].device_id == "130600112764"
    assert history[0].temperature == 4.5
