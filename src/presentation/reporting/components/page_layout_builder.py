"""Page layout helpers for the PDF engine."""


class PageLayoutBuilder:
    def __init__(self, page_size=None, margins=None) -> None:
        self.page_size = page_size
        self.margins = margins or (72, 72, 72, 72)  # default 1-inch margins

    def apply(self, doc):
        """Configures a reportlab document object with page size and margins."""
        if self.page_size is not None and hasattr(doc, "pagesize"):
            doc.pagesize = self.page_size
        if hasattr(doc, "topMargin"):
            doc.topMargin = self.margins[0]
            doc.bottomMargin = self.margins[1]
            doc.leftMargin = self.margins[2]
            doc.rightMargin = self.margins[3]
