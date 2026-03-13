"""
دوال مساعدة للاستيراد الآمن للوحدات.
تدعم تسجيل تفصيلي، تحميل ديناميكي حسب البيئة، وتجميع التقارير.
"""
import logging
import os
from typing import Any, Optional, Dict, List
from importlib import util
from functools import lru_cache

logger = logging.getLogger(__name__)

# تخزين سجل الاستيرادات الفاشلة للتقرير لاحقاً
_missing_imports: List[Dict[str, Any]] = []


def safe_import(
    module_path: str, 
    attr: Optional[str] = None, 
    fallback: Any = None,
    required_in: Optional[List[str]] = None,
    log_level: str = "debug"
) -> Any:
    """
    استيراد آمن للوحدات مع fallback وتسجيل تفصيلي.

    Args:
        module_path: مسار الوحدة (مثل 'src.shared.language_manager')
        attr: اسم الكائن المراد استيراده (اختياري)
        fallback: القيمة الاحتياطية في حال فشل الاستيراد
        required_in: قائمة البيئات التي تتطلب هذه الوحدة (مثل ['prod'])
        log_level: مستوى التسجيل للفشل ('debug', 'info', 'warning', 'error')

    Returns:
        الكائن المستورد أو القيمة الاحتياطية
    """
    current_env = os.getenv("ENV", "dev").lower()
    
    try:
        mod = __import__(module_path, fromlist=[attr] if attr else [])
        if attr:
            result = getattr(mod, attr)
        else:
            result = mod
            
        # تسجيل نجاح الاستيراد في وضع verbose
        logger.debug(f"✅ تم استيراد {module_path}" + (f".{attr}" if attr else ""))
        return result
        
    except (ImportError, AttributeError) as e:
        # تحديد مستوى التسجيل بناءً على البيئة
        is_required = required_in and current_env in [env.lower() for env in required_in]
        
        log_msg = f"⚠️ تعذر استيراد {module_path}"
        if attr:
            log_msg += f".{attr}"
        log_msg += f": {e}"
        
        if is_required:
            # إذا كانت الوحدة مطلوبة في هذه البيئة، نسجل كخطأ
            logger.error(log_msg)
            _missing_imports.append({
                "module": module_path,
                "attr": attr,
                "error": str(e),
                "environment": current_env,
                "required": True
            })
        else:
            # وإلا نسجل حسب المستوى المطلوب
            log_func = getattr(logger, log_level.lower(), logger.debug)
            log_func(log_msg)
            _missing_imports.append({
                "module": module_path,
                "attr": attr,
                "error": str(e),
                "environment": current_env,
                "required": False
            })
        
        return fallback


@lru_cache(maxsize=32)
def check_module_available(module_path: str) -> bool:
    """
    التحقق من توفر وحدة دون استيرادها (باستخدام importlib).
    
    Args:
        module_path: مسار الوحدة
        
    Returns:
        True إذا كانت الوحدة متوفرة
    """
    return util.find_spec(module_path) is not None


def get_missing_imports_report(include_all: bool = False) -> Dict[str, Any]:
    """
    الحصول على تقرير بالواردات الفاشلة.
    
    Args:
        include_all: تضمين جميع الواردات (حتى الناجحة)
        
    Returns:
        تقرير بالواردات الفاشلة
    """
    return {
        "total_missing": len(_missing_imports),
        "required_missing": sum(1 for i in _missing_imports if i["required"]),
        "by_environment": {
            env: [i for i in _missing_imports if i["environment"] == env]
            for env in set(i["environment"] for i in _missing_imports)
        },
        "details": _missing_imports if include_all else None
    }


def clear_missing_imports() -> None:
    """مسح سجل الواردات الفاشلة (للاستخدام في الاختبارات)."""
    _missing_imports.clear()
