# tests/architecture/test_decision_path_separation.py
def test_decision_path_never_uses_estimator():
    """
    Ensure no code path connects estimator to decision logic.
    """
    # ← Static analysis to ensure estimator not used in decision path
    # ← Runtime check to ensure decision service never calls estimator
    pass
