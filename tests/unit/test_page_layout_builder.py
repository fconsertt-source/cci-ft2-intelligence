"""Basic tests for the PageLayoutBuilder stub."""

from src.presentation.reporting.components.page_layout_builder import \
    PageLayoutBuilder


def test_layout_builder_no_reportlab():
    # builder should not raise even if doc object has expected attrs
    class Dummy:
        pass

    doc = Dummy()
    plb = PageLayoutBuilder(page_size=(100, 200), margins=(10, 10, 10, 10))
    # apply should not error when doc lacks attributes
    plb.apply(doc)

    # create object with attributes
    class Doc:
        pass

    doc2 = Doc()
    doc2.pagesize = None
    doc2.topMargin = 0
    doc2.bottomMargin = 0
    doc2.leftMargin = 0
    doc2.rightMargin = 0
    plb.apply(doc2)
    assert doc2.pagesize == (100, 200)
    assert doc2.topMargin == 10
    assert doc2.bottomMargin == 10
