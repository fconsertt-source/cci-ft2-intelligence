from src.presentation.reporting.components.table_builder import TableBuilder


def test_table_builder_no_reportlab(monkeypatch):
    # force imports of any reportlab submodule to fail
    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("reportlab"):
            raise ImportError
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    tb = TableBuilder("Helvetica", {})
    rows = [{"a": 1}, {"b": 2}]
    result = tb.build(rows, "official")
    assert isinstance(result, list)
    # should no longer be simple strings; expect Flowable-like objects
    assert all(hasattr(x, "getKeepWithNext") for x in result)


def test_table_builder_with_reportlab(monkeypatch):
    try:
        from reportlab.platypus import Table
    except ImportError:
        import pytest

        pytest.skip("reportlab not installed")
    styles = {}
    tb = TableBuilder("Helvetica", styles)
    rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    result = tb.build(rows, "official")
    # should contain a Table instance
    assert any(getattr(e, "__class__", None).__name__ == "Table" for e in result)
