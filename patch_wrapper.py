#!/usr/bin/env python3
import re

# قراءة الملف الحالي
with open(
    "src/infrastructure/adapters/reporting/unified_pdf_generator_wrapper.py",
    "r",
    encoding="utf-8",
) as f:
    content = f.read()

# 1. إضافة ARABIC_SUPPORT_AVAILABLE في الأعلى
if "ARABIC_SUPPORT_AVAILABLE" not in content:
    content = content.replace(
        "from typing import TYPE_CHECKING",
        """from typing import TYPE_CHECKING

# ✅ التحقق من دعم العربية
ARABIC_SUPPORT_AVAILABLE = False
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT_AVAILABLE = True
except ImportError:
    pass""",
    )

# 2. إضافة دالة _shape_arabic
if "def _shape_arabic" not in content:
    content = content.replace(
        "class UnifiedPDFGeneratorWrapper:",
        '''def _shape_arabic(text: str) -> str:
    """Apply Arabic reshaping + bidi if available."""
    if ARABIC_SUPPORT_AVAILABLE:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            pass
    return text


class UnifiedPDFGeneratorWrapper:''',
    )

# حفظ الملف المصحح
with open(
    "src/infrastructure/adapters/reporting/unified_pdf_generator_wrapper.py",
    "w",
    encoding="utf-8",
) as f:
    f.write(content)

print("✅ Patch applied successfully")
