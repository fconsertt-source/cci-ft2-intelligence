"""Centralized message repository to prevent linguistic drift in user-facing text.
Design principle: Domain emits codes → Presentation maps to human-readable text.
All user-facing text MUST flow through this module.
"""

from types import MappingProxyType
from typing import Any, Final

# Immutable message map - prevents accidental modification at runtime
_MESSAGE_MAP: Final = MappingProxyType({
    # ========================================================================
    # Domain Decision Codes → Human-Readable Messages
    # ========================================================================
    # Decision outcomes from Domain layer rules engine
    'DECISION_ACCEPTED': "✅ تم قبول اللقاح - ضمن المواصفات",
    'DECISION_REJECTED_FREEZE': "❌ رُفض بسبب التجميد",
    'DECISION_REJECTED_HEAT_CRITICAL': "❌ رُفض بسبب الحرارة الحرجة",
    'DECISION_REJECTED_HEAT_WARNING': "⚠️ إنذار: تعرض للحرارة (احتياطي الاستقرار منخفض)",
    'DECISION_NO_DATA': "⚠️ لا توجد بيانات كافية للتقييم",
    'DECISION_THAW_EXPIRED': "❌ انتهت صلاحية اللقاح بعد الذوبان",
    
    # VVM Stage display text (mapped from Domain codes)
    'VVM_STAGE_1': "المرحلة 1 (أبيض)",
    'VVM_STAGE_2': "المرحلة 2 (أصفر فاتح)",
    'VVM_STAGE_3': "المرحلة 3 (أصفر غامق)",
    'VVM_STAGE_4': "المرحلة 4 (أرجواني)",
    'VVM_STAGE_INVALID': "غير صالح",
    
    # Alert levels (mapped from Domain calculations)
    'ALERT_LEVEL_GREEN': "🟢 أخضر (آمن)",
    'ALERT_LEVEL_YELLOW': "🟡 أصفر (احتياطي منخفض)",
    'ALERT_LEVEL_RED': "🔴 أحمر (حرج)",
    
    # ========================================================================
    # Pipeline & Infrastructure Messages (Presentation Layer Concerns)
    # ========================================================================
    # General pipeline execution
    'PIPELINE_START': "🚀 بدء تشغيل خط معالجة FT2",
    'PIPELINE_COMPLETE': "🏁 اكتمل خط المعالجة. انظر {output_dir} للنتائج",
    'PIPELINE_SUMMARY_TITLE': "ملخص تشغيل خط المعالجة",
    'FILES_FOUND_TO_PROCESS': "📁 وجد {count} ملف للمعالجة في {path}",
    'FILES_PROCESSED': "الملفات المعالجة: {processed_count} من أصل {total_count}",
    'FILES_FAILED': "الملفات الفاشلة: {failed_count}",
    'FAILED_FILES_LIST_TITLE': "الملفات الفاشلة:",
    'CENTER_REPORT_GENERATED': "تقرير المراكز: {path}",
    'DETAILED_REPORTS_GENERATED': "التقارير التفصيلية: {path}",
    
    # Simple pipeline simulation
    'SIMPLE_PIPELINE_START': "🚀 بدء التشغيل المبسط...",
    'SIMPLE_PIPELINE_STEP_1': "🧪 الخطوة 1: إنشاء بيانات اختبار...",
    'SIMPLE_PIPELINE_TEST_DATA_CREATED': "✅ تم إنشاء بيانات الاختبار",
    'SIMPLE_PIPELINE_STEP_2': "🔄 الخطوة 2: محاكاة معالجة البيانات...",
    'SIMPLE_PIPELINE_FAKE_REPORT_CREATED': "✅ تم إنشاء التقرير الوهمي",
    'SIMPLE_PIPELINE_MAPPED_TO_DTO': "Mapped {count} rows to CenterDTOs (no Entities passed outside Domain)",
    'SIMPLE_PIPELINE_REPORT_GENERATED': "✅ تم إنشاء التقرير عبر generate_centers_report: {path}",
    'SIMPLE_PIPELINE_SUCCESS': "🎉 اكتمل التشغيل المبسط بنجاح!",
    'SIMPLE_PIPELINE_FAILED': "❌ فشل التشغيل المبسط",
    
    # PDF report generation
    'PDF_GENERATION_START': "📄 إنشاء تقرير PDF احترافي",
    'PDF_READING_DATA': "📊 قراءة البيانات من: {path}",
    'PDF_GENERATION_IN_PROGRESS': "🔄 جاري إنشاء التقرير...",
    'PDF_GENERATION_SUCCESS': "✅ تم إنشاء التقرير بنجاح!",
    'PDF_LOCATION': "📍 الموقع: {path}",
    'PDF_SIZE': "📏 الحجم: {size:.1f} KB",
    'PDF_AUTO_OPENED': "📂 تم فتح التقرير تلقائياً",
    'PDF_MANUAL_OPEN_HINT': "💡 يمكنك فتح التقرير يدوياً من المسار أعلاه",
    'PDF_GENERATION_FAILED': "❌ فشل في إنشاء التقرير",
    'PDF_SOURCE_FILE_MISSING': "❌ ملف التقرير غير موجود: {path}",
    'PDF_RUN_PIPELINE_HINT': "⚠️  قم بتشغيل النظام أولاً:",
    'PDF_RUN_PIPELINE_CMD': "   python -m scripts.run_ft2_pipeline --legacy",
    
    # Backup operations
    'BACKUP_CREATION_START': "📦 جاري إنشاء نسخة احتياطية للمشروع: {name}",
    'BACKUP_TARGET_PATH': "📂 المسار المستهدف: {path}",
    'BACKUP_CREATION_SUCCESS': "✅ تم إنشاء النسخة الاحتياطية بنجاح!",
    'BACKUP_SIZE': "📊 الحجم: {size:.2f} MB",
    'BACKUP_LOCATION': "📍 الموقع: {path}",
    'BACKUP_CREATION_FAILED': "❌ فشل إنشاء النسخة الاحتياطية: {error}",
    
    # Debug operations
    'DEBUG_CLEANING_FILES': "🧹 تنظيف الملفات التالفة في {path}",
    'DEBUG_DIR_NOT_FOUND': "المجلد {path} غير موجود.",
    'DEBUG_FILE_DELETED': "🗑️ تم حذف: {file} ({reason})",
    'DEBUG_NO_BAD_FILES': "✨ لم يتم العثور على ملفات تالفة.",
    'DEBUG_CLEANED_COUNT': "✅ تم تنظيف {count} ملف.",
    'DEBUG_CLEAN_HINT': "\n💡 تلميح: لتنظيف الملفات التالفة تلقائياً، شغّل: python scripts/debug_ft2.py --clean",
    
    # Warnings & Errors
    'NO_FILES_TO_PROCESS': "⚠️ لم يتم العثور على ملفات للمعالجة في: {path}",
    'EMPTY_INPUT_DIR_HINT': "💡 تلميح: المجلد فارغ. يمكنك إنشاء بيانات اختبار باستخدام الخيار: --generate-data",
    'CRITICAL_CONFIG_LOAD_FAILED': "❌ خطأ حرج في تحميل تكوين المراكز: {error}",
    'CONFIG_LOAD_FAILED_STOP': "فشل تحميل تكوين المراكز. تم إيقاف التشغيل لسلامة البيانات.",
    'FILE_PROCESSING_FAILED': "❌ فشل معالجة {file}: {error}",
    'UNEXPECTED_ERROR': "❌ خطأ غير متوقع: {error}",
    
    # ========================================================================
    # Device Report Messages (Phase 6)
    # ========================================================================
    "DEVICE_REPORT_GENERATED": "✅ تم إنشاء تقرير الجهاز {device_id} في: {path}",
    "DEVICE_NOT_FOUND": "❌ الجهاز {device_id} غير موجود في البيانات — تحقق من المعرف",
    "DEVICE_REPORTS_NOT_YET_IMPLEMENTED": "⚠️ ميزة تقارير جميع الأجهزة قيد التطوير (Phase 6.1)",
    "DEVICE_REPORTS_GENERATION_FAILED": "❌ فشل توليد تقارير الأجهزة: {error}",
    
    # CLI
    "DEVICE_DATA_SOURCE_MISSING": "❌ ملف البيانات المصدر غير موجود: {path}",
    'CLI_DESCRIPTION': 'نظام متكامل لمعالجة ملفات FT2 لمراقبة سلسلة التبريد',
})

# Public immutable interface
MESSAGE_MAP = _MESSAGE_MAP


class MessageProvider:
    """Centralized provider for all user-facing messages.
    
    Architectural contract:
      - Domain layer MUST return codes only (e.g., "ACCEPTED")
      - Presentation layer MUST map codes → text via this provider
      - NO hardcoded user messages allowed outside this module
    """
    # ✅ مستخرج من run_windows_friendly.ps1 — تجربة مستخدم مُختبرة
    CLI_DECISION_SYMBOLS = {
        "ACCEPTED": ("[+]", "green"),
        "WARNING": ("[!]", "yellow"),
        "REJECTED": ("[X]", "red"),
        "NO_DATA": ("[?]", "gray"),
    }
    
    @classmethod
    def get_decision_symbol(cls, decision: str) -> str:
        for key, (symbol, _) in cls.CLI_DECISION_SYMBOLS.items():
            if key in decision:
                return symbol
        return "[?]"
    
    @staticmethod
    def get(key: str, **kwargs: Any) -> str:
        """
        Retrieves and formats a message from the central immutable map.
        
        Args:
            key: Message key from MESSAGE_MAP (e.g., 'DECISION_ACCEPTED')
            **kwargs: Values to substitute into message placeholders
            
        Returns:
            Formatted Arabic message string
            
        Guarantees:
          - Always returns a string (never raises for missing keys)
          - Graceful degradation on formatting errors
          - Immutable source prevents runtime modification
        """
        message = MESSAGE_MAP.get(key)
        if message is None:
            return f"⚠️ رسالة مفقودة: {key}"
        
        try:
            return message.format(**kwargs)
        except (KeyError, TypeError):
            # Return raw message on formatting failure (graceful degradation)
            return f"⚠️ خطأ تنسيق: {message}"
# Backward compatibility alias
MessageMap = MessageProvider
