#!/usr/bin/env python3
"""
مدير اللغة (Language Manager) للحارس الرقمي
✅ Singleton لضمان مصدر واحد للترجمات
✅ دعم المتغيرات في الترجمات
✅ Fallback للعربية ← الإنجليزية ← المفتاح
✅ تنظيف المفاتيح من المسافات الزائدة
"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LanguageManager:
    _instance = None
    _current_lang = "ar"  # default Arabic
    _translations = {}
    _fallback_chain = ["ar", "en"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_language(
        self, lang_code: str, translations_dir: Optional[Path] = None
    ) -> None:
        """تحميل ملف ترجمة لغة معينة"""
        if translations_dir is None:
            # ✅ البحث في مجلد locales بجانب هذا الملف
            translations_dir = Path(__file__).parent / "locales"

        file_path = translations_dir / f"{lang_code}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Translation file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_translations = json.load(f)
            # ✅ تنظيف المفاتيح والقيم من المسافات الزائدة
            self._translations[lang_code] = {
                k.strip(): v.strip() if isinstance(v, str) else v
                for k, v in raw_translations.items()
            }

        logger.info(
            f"Loaded {lang_code} translations: {len(self._translations[lang_code])} keys"
        )

        # Always move the newly-loaded language to the front of the fallback chain
        if lang_code in self._fallback_chain:
            self._fallback_chain.remove(lang_code)
        self._fallback_chain.insert(0, lang_code)
        self._current_lang = lang_code

    def get(self, key: str, default=None, **kwargs) -> str:
        """
        الحصول على النص المترجم.
        - key: مفتاح النص
        - default: قيمة افتراضية في حال عدم وجود المفتاح
        - **kwargs: متغيرات للاستبدال في النص
        """
        key = key.strip()
        for lang in self._fallback_chain:
            lang_dict = self._translations.get(lang, {})
            if key in lang_dict:
                template = lang_dict[key]
                text = template.format(**kwargs) if kwargs else template
                if self._current_lang == "ar":
                    text = self._shape_arabic(text)
                return text

        # Fallback: القيمة الافتراضية أو المفتاح نفسه
        return default if default is not None else key

    def get_raw(self, key: str, **kwargs) -> str:
        """الحصول على النص المترجم بدون Arabic shaping - للاستخدام في title bar."""
        key = key.strip()
        for lang in self._fallback_chain:
            lang_dict = self._translations.get(lang, {})
            if key in lang_dict:
                template = lang_dict[key]
                return template.format(**kwargs) if kwargs else template
        return key

    def _shape_arabic(self, text: str) -> str:
        """تطبيق Arabic reshaping و bidi لعرض صحيح في Tkinter."""
        try:
            import re

            import arabic_reshaper
            from bidi.algorithm import get_display

            reshaped = arabic_reshaper.reshape(text)
            # النصوص المختلطة تحتاج base_dir='R' للحفاظ على ترتيب العناصر
            has_latin = bool(re.search(r"[a-zA-Z0-9]", text))
            if has_latin:
                return get_display(reshaped, base_dir="R")
            return get_display(reshaped)
        except ImportError:
            return text

    def set_language(self, lang_code: str) -> None:
        """تغيير اللغة (يجب أن تكون محملة مسبقاً)"""
        if lang_code in self._translations:
            self._current_lang = lang_code
        else:
            raise ValueError(f"Language '{lang_code}' not loaded")

    @property
    def current_language(self) -> str:
        return self._current_lang

    @property
    def is_rtl(self) -> bool:
        """هل اللغة الحالية تكتب من اليمين لليسار؟"""
        return self._current_lang == "ar"


# Global instance for convenience
lang = LanguageManager()
