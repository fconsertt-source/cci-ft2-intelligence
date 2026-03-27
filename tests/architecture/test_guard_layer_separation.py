import ast


def test_trial_policy_has_no_thermal_dependencies():
    """Ensure TrialPolicy does NOT import thermal or regulatory modules."""
    path = "src/domain/policies/trial_policy.py"
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    forbidden_modules = {
        "her",
        "ccm",
        "q10",
        "thermal",
        "regulatory",
        "calculator",
        "domain.services",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if any(mod in node.module.lower() for mod in forbidden_modules):
                raise AssertionError(
                    f"TrialPolicy imports forbidden module: {node.module}"
                )

    # Also check for direct attribute access
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if hasattr(node.value, "id") and node.value.id == "src":
                if "thermal" in node.attr.lower():
                    raise AssertionError(
                        f"Found thermal reference in TrialPolicy: {node.attr}"
                    )

    assert True, "TrialPolicy is clean"
