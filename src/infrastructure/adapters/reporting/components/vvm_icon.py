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
        black = None

        class Color:
            def __init__(self, *args, **kwargs):
                pass


class VVMIcon(Flowable):
    def __init__(self, size, her_pct):
        super().__init__()
        self.size = size
        self.width = size
        self.height = size
        self.her = her_pct / 100.0

    def draw(self):
        if not _HAS_RL:
            return
        radius = self.size / 2.0
        circle_gray = 0.55
        self.canv.setStrokeColor(colors.black)
        self.canv.setLineWidth(0.5)
        self.canv.setFillColor(colors.Color(circle_gray, circle_gray, circle_gray))
        self.canv.circle(radius, radius, radius, stroke=1, fill=1)

        if self.her < 0.5:
            val = 1.0
            has_stroke = 1
        elif self.her < 0.82:
            val = 0.8
            has_stroke = 1
        elif 0.82 <= self.her < 1.05:
            val = circle_gray
            has_stroke = 0
        else:
            val = 0.2
            has_stroke = 1

        self.canv.setFillColor(colors.Color(val, val, val))
        sq_size = self.size * 0.5
        offset = (self.size - sq_size) / 2.0

        if not has_stroke:
            self.canv.setStrokeColor(
                colors.Color(circle_gray, circle_gray, circle_gray)
            )
        else:
            self.canv.setStrokeColor(colors.black)

        self.canv.setLineWidth(0.3)
        self.canv.rect(offset, offset, sq_size, sq_size, stroke=has_stroke, fill=1)
