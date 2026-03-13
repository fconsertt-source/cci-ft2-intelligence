"""Chart/graph builder for reports (initially matplotlib-backed)."""

from typing import List


class ChartBuilder:
    def __init__(self, theme_color: str) -> None:
        self.theme_color = theme_color

    def build(self, records: List[dict], report_type: str) -> list:
        """Return Flowable elements representing charts for the given records.

        If matplotlib and reportlab are available, generate a simple bar chart
        showing the first field of each record.  Otherwise return a placeholder
        token that allows downstream code to proceed.
        """
        try:
            from io import BytesIO

            import matplotlib.pyplot as plt
            from reportlab.platypus import Image, Spacer
        except Exception:
            # cannot build a chart; placeholder must still be Flowable
            # use Paragraph+Spacer if reportlab available, otherwise a minimal
            # dummy object with the Flowable API so Platypus doesn't crash.
            try:
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import Paragraph, Spacer

                styles = getSampleStyleSheet()
                text = "Chart unavailable"
                return [Paragraph(text, styles.get("Normal")), Spacer(1, 12)]
            except Exception:

                class _DummyFlowable:
                    def getKeepWithNext(self):
                        return None

                return [_DummyFlowable()]

        if not records:
            # nothing to plot – use same Flowable placeholder logic as above
            try:
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import Paragraph, Spacer

                styles = getSampleStyleSheet()
                text = "Chart unavailable"
                return [Paragraph(text, styles.get("Normal")), Spacer(1, 12)]
            except Exception:

                class _DummyFlowable:
                    def getKeepWithNext(self):
                        return None

                return [_DummyFlowable()]

        key = list(records[0].keys())[0]
        values = [r.get(key, 0) or 0 for r in records]
        plt.figure(figsize=(4, 2))
        plt.bar(range(len(values)), values, color=self.theme_color)
        buf = BytesIO()
        plt.savefig(buf, format="PNG")
        plt.close()
        buf.seek(0)
        img = Image(buf, width=200, height=100)
        return [img, Spacer(1, 12)]
