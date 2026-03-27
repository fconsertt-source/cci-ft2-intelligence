from src.presentation.reporting.components.chart_builder import ChartBuilder


def test_chart_builder_placeholder():
    cb = ChartBuilder("#000")
    out = cb.build([], "official")
    # placeholder must be Flowable objects, not raw strings
    assert isinstance(out, list) and len(out) > 0
    assert all(hasattr(e, "getKeepWithNext") for e in out)


def test_chart_builder_with_data(monkeypatch):
    # verify flowables when reportlab + matplotlib present
    try:
        import matplotlib.pyplot  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("matplotlib or reportlab unavailable")
    records = [{"a": 1}, {"a": 3}, {"a": 2}]
    cb = ChartBuilder("#ff0000")
    out = cb.build(records, "official")
    assert any(getattr(e, "__class__", None).__name__ == "Image" for e in out)
