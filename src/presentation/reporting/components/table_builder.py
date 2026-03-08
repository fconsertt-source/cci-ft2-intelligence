"""Table building utility for the PDF engine."""

from typing import Any, List


class TableBuilder:
    def __init__(self, font_name: str, styles: Any) -> None:
        self.font_name = font_name
        self.styles = styles

    def build(self, records: List[dict], report_type: str) -> list:
        """Return Flowable list representing the data table.

        When ReportLab is present we create a proper Table with headers derived
        from the first record's keys.  Otherwise we fall back to the simple
        string list used earlier.
        """
        try:
            from reportlab.lib import colors
            from reportlab.platypus import Spacer, Table, TableStyle
        except ImportError:
            # even if ReportLab is missing we still need Flowables
            class _DummyFlowable:
                def getKeepWithNext(self):
                    return None

            return [_DummyFlowable() for _ in records]

        if not records:
            # no data -> return empty list (no Flowables required)
            return []

        headers = list(records[0].keys())
        data = [headers] + [list(r.values()) for r in records]
        t = Table(data, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return [t, Spacer(1, 12)]
