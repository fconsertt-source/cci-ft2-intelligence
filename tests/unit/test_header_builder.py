try:
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    getSampleStyleSheet = None

from src.presentation.reporting.components.header_builder import (
    FooterBuilder,
    HeaderBuilder,
)


def make_dto():
    class Dummy:
        pass

    return Dummy()


def test_header_builder_default():
    if getSampleStyleSheet is None:
        import pytest

        pytest.skip("reportlab not installed")
    styles = getSampleStyleSheet()
    hb = HeaderBuilder("Helvetica", styles)
    elems = hb.build("official", make_dto())
    assert elems, "Header elements should not be empty"
    assert any("Official" in getattr(e, "text", "") for e in elems)


def test_footer_builder():
    if getSampleStyleSheet is None:
        import pytest

        pytest.skip("reportlab not installed")
    styles = getSampleStyleSheet()
    fb = FooterBuilder("Helvetica", styles)
    elems = fb.build(make_dto())
    assert elems
    # elements may be strings or flowables
    texts = []
    for e in elems:
        if isinstance(e, str):
            texts.append(e)
        else:
            texts.append(getattr(e, "text", ""))
    assert any("Generated" in t for t in texts)
