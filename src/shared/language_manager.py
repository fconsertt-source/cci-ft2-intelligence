#!/usr/bin/env python3
"""
مدير اللغة (Language Manager) للحارس الرقمي

✅ Singleton لضمان مصدر واحد للترجمات
✅ دعم المتغيرات في الترجمات
✅ Fallback للعربية ← الإنجليزية ← المفتاح
"""

import json
from pathlib import Path
from typing import Optional


class LanguageManager:
    _instance = None
    _current_lang = "ar"  # default Arabic
    _translations = {}
    _fallback_chain = ["ar", "en"]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_language(self, lang_code: str, translations_dir: Path = Path("translations")) -> None:
        """تحميل ملف ترجمة لغة معينة"""
        file_path = translations_dir / lang_code / "messages.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Translation file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            self._translations[lang_code] = json.load(f)
        
        if lang_code not in self._fallback_chain:
            self._fallback_chain.insert(0, lang_code)
        
        self._current_lang = lang_code
    
    def get(self, key: str, **kwargs) -> str:
        """الحصول على النص المترجم مع إمكانية استبدال المتغيرات"""
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
