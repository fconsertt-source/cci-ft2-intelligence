try:
    from reportlab.lib import colors
    from reportlab.platypus import Flowable

    _HAS_RL = True
except ImportError:  # pragma: no cover
    _HAS_RL = False

    class Flowable:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, item):
            return lambda *a, **k: None

    class colors:
        white = None


class AlertCircle(Flowable):
    def __init__(self, size, color):
        super().__init__()
        self.size = size
        self.width = size
        self.height = size
        self.color = color

    def draw(self):
        if not _HAS_RL:
            return
        self.canv.setFillColor(self.color)
        self.canv.setStrokeColor(colors.white)
        self.canv.setLineWidth(0.5)
        self.canv.circle(self.size / 2, self.size / 2, self.size / 2, stroke=1, fill=1)
