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

    def get(self, key: str, **kwargs) -> str:
        """الحصول على النص المترجم مع إمكانية استبدال المتغيرات"""
        # ✅ تنظيف المفتاح من المسافات الزائدة
        key = key.strip()

        for lang in self._fallback_chain:
            lang_dict = self._translations.get(lang, {})
            if key in lang_dict:
                template = lang_dict[key]
                return template.format(**kwargs) if kwargs else template

        # Fallback to key itself
        return key

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
