try:
    from reportlab.lib import colors
    from reportlab.platypus import Flowable

    _HAS_RL = True
except ImportError:  # pragma: no cover - missing dependency
    _HAS_RL = False

    class Flowable:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, item):
            return lambda *a, **k: None

    class colors:
        lightgrey = None
        black = None


class StabilityBar(Flowable):
    """A custom progress bar with a pointer for Stability Budget."""

    def __init__(self, width, height, pct, color):
        super().__init__()
        self.width = width
        self.height = height
        self.pct = min(100, max(0, pct))
        self.color = color

    def draw(self):
        if not _HAS_RL:
            return
        self.canv.setLineWidth(0.5)
        self.canv.setStrokeColor(colors.lightgrey)
        self.canv.roundRect(0, 0, self.width, self.height, 2, stroke=1, fill=0)
        fill_width = (self.pct / 100.0) * self.width
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, fill_width, self.height, 2, stroke=0, fill=1)
        pointer_pos = fill_width
        self.canv.setStrokeColor(colors.black)
        self.canv.setLineWidth(1)
        self.canv.line(pointer_pos, -2, pointer_pos, self.height + 2)
