import json
from pathlib import Path
import pytest
import logging

logger = logging.getLogger(__name__)

class TestLocalesCompleteness:
    """
    التحقق من اكتمال ملفات الترجمة وتزامنها.
    
    المبدأ: en.json هو المصدر الأساسي، ar.json يجب أن يحتوي على المفاتيح الحرجة.
    """
    
    # مفاتيح حرجة يجب أن تكون موجودة في كلا اللغتين (للتقارير والمقاييس)
    CRITICAL_KEYS = [
        "SSOT_STATUS",
        "DATA_QUALITY_SCORE", 
        "PIPELINE_SUMMARY",
        "status.ready",
        "msg.success",
        "VISUAL_REPORT_TECHNICAL",
        "VISUAL_REPORT_OFFICIAL", 
        "VISUAL_REPORT_ARABIC",
    ]
    
    # مفاتيح إضافية يُفضل وجودها لكن لا نرفض البناء إذا نقصت
    PREFERRED_KEYS = [
        "button.ok", "button.cancel", "error.file_not_found", "msg.confirm"
    ]

    @pytest.fixture
    def ar_locale(self):
        path = Path("src/shared/locales/ar.json")
        return json.loads(path.read_text(encoding="utf-8"))

    @pytest.fixture
    def en_locale(self):
        path = Path("src/shared/locales/en.json")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_critical_keys_in_arabic(self, ar_locale):
        """المفاتيح الحرجة يجب أن تكون موجودة في العربية"""
        missing = [k for k in self.CRITICAL_KEYS if k not in ar_locale]
        assert not missing, f"مفاتيح حرجة مفقودة في ar.json: {missing}"

    def test_critical_keys_in_english(self, en_locale):
        """المفاتيح الحرجة يجب أن تكون موجودة في الإنجليزية"""
        missing = [k for k in self.CRITICAL_KEYS if k not in en_locale]
        assert not missing, f"Critical keys missing in en.json: {missing}"

    def test_ar_and_en_critical_sync(self, ar_locale, en_locale):
        """المفاتيح الحرجة يجب أن تكون متزامنة بين اللغتين"""
        ar_critical = {k: ar_locale[k] for k in self.CRITICAL_KEYS if k in ar_locale}
        en_critical = {k: en_locale[k] for k in self.CRITICAL_KEYS if k in en_locale}
        
        # التحقق من أن جميع المفاتيح الحرجة موجودة في كليهما
        assert set(ar_critical.keys()) == set(en_critical.keys()), \
            f"Critical keys mismatch: AR={set(ar_critical.keys())}, EN={set(en_critical.keys())}"

    def test_locale_coverage_warning(self, ar_locale, en_locale):
        """
        تحذير (ليس فشل) إذا كانت هناك فجوات في التغطية.
        يُسجّل في اللوغ للاطلاع والفحص المستقبلي.
        """
        ar_keys = set(ar_locale.keys())
        en_keys = set(en_locale.keys())
        
        only_in_ar = ar_keys - en_keys
        only_in_en = en_keys - ar_keys
        
        # تسجيل تحذير للفجوات (لا يفشل الاختبار)
        if only_in_ar:
            logger.warning(f"Keys only in Arabic (consider adding to en.json): {only_in_ar}")
        if only_in_en:
            logger.warning(f"Keys only in English (consider adding to ar.json): {only_in_en}")
        
        # التحقق من أن الفجوة ليست كبيرة جداً (>50% نقص في العربية)
        if len(ar_keys) < len(en_keys) * 0.5:
            pytest.fail(
                f"Arabic locale coverage too low: {len(ar_keys)}/{len(en_keys)} keys "
                f"({len(ar_keys)/len(en_keys)*100:.1f}%). Please complete translations."
            )
        
        # إذا كانت الفجوة معقولة، نمرر الاختبار مع تحذير
        if only_in_en:
            logger.info(f"Locale sync: {len(ar_keys)}/{len(en_keys)} keys covered ({len(ar_keys)/len(en_keys)*100:.1f}%)")
