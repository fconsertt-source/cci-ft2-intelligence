import re
from typing import Final

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    _BIDI_AVAILABLE: Final = True
except Exception:
    _BIDI_AVAILABLE = False


_ARABIC_RANGE = re.compile(r"[\u0600-\u06FF]")
_LATIN_RANGE = re.compile(r"[A-Za-z]")


def contains_arabic(text: str) -> bool:
    return bool(_ARABIC_RANGE.search(text or ""))


def is_mixed_direction(text: str) -> bool:
    if not text:
        return False
    return bool(_ARABIC_RANGE.search(text) and _LATIN_RANGE.search(text))


def shape_arabic_visual(text: str) -> str:
    """Shaping بصري للحالات المختلطة فقط."""
    if not text or not _BIDI_AVAILABLE:
        return text

    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def prepare_text_for_pdf(text: str) -> str:
    """
    ⭐ القرار الذكي:
    - عربي صرف → لا shaping (نحافظ على المنطقي)
    - مختلط → shaping بصري
    - غير عربي → كما هو
    """
    if not text:
        return text

    if not contains_arabic(text):
        return text

    if is_mixed_direction(text):
        return shape_arabic_visual(text)

    return text
