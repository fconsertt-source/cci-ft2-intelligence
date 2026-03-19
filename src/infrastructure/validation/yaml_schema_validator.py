# src/infrastructure/validation/yaml_schema_validator.py


def validate_vaccine_yaml(data: dict):

    if "vaccines" not in data:
        raise ValueError("Missing vaccines section")

    for vid, spec in data["vaccines"].items():

        required = ["q10_factor", "shelf_life_days"]

        for field in required:
            if field not in spec:
                raise ValueError(f"{vid}: missing {field}")

        if "max_temp" not in spec:
            raise ValueError(f"{vid}: missing max_temp")

        if spec.get("freeze_range"):
            if len(spec["freeze_range"]) != 2:
                raise ValueError(f"{vid}: invalid freeze_range")
