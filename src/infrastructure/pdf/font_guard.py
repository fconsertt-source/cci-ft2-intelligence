from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class FontGuardError(RuntimeError):
    pass


def register_arabic_font_strict(name: str, path: str) -> None:
    p = Path(path)

    if not p.exists():
        raise FontGuardError(f"Arabic font not found: {path}")

    # ⭐ validate=1 يفرض فحص الخط
    font = TTFont(name, str(p), validate=1)
    pdfmetrics.registerFont(font)


def assert_font_embedded(pdf_bytes: bytes) -> None:
    """
    فحص سريع مؤسسي.
    """
    if b"/FontFile2" not in pdf_bytes:
        raise AssertionError("Font not embedded in PDF")
