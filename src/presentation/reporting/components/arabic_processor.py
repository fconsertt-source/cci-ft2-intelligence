"""Arabic text processing utilities (reshaping + bidi)."""

ARABIC_LIBS_AVAILABLE = False
arabic_reshaper = None  # will be replaced if import succeeds
get_display = lambda s: s

try:
    import arabic_reshaper as _reshaper
    from bidi.algorithm import get_display as _get_display

    arabic_reshaper = _reshaper
    get_display = _get_display
    ARABIC_LIBS_AVAILABLE = True
except ImportError:
    # fallback no-op if libraries not installed
    pass


def shape(text: str) -> str:
    """Return OCR-friendly shaped text for Arabic scripts.

    When the arabic_reshaper and python-bidi libs are available the
    output will be re‑ordered and shaped appropriately; otherwise the
    original string is returned unchanged.
    """
    if not ARABIC_LIBS_AVAILABLE or not text:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text
