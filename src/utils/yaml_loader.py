import yaml
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def load_yaml(file_path: str) -> Any:
    """
    تحميل ملف YAML
    
    Args:
        file_path: مسار ملف YAML
        
    Returns:
        محتوى الملف المحلل
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        logger.info(f"تم تحميل YAML من: {file_path}")
        return content
        
    except FileNotFoundError:
        logger.error(f"ملف YAML غير موجود: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"خطأ في تحليل YAML: {e}")
        raise
    except Exception as e:
        logger.error(f"خطأ غير متوقع في تحميل YAML: {e}")
        raise

def save_yaml(data: Any, file_path: str):
    """
    حفظ بيانات إلى ملف YAML
    
    Args:
        data: البيانات للحفظ
        file_path: مسار ملف YAML
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"تم حفظ YAML إلى: {file_path}")
        
    except Exception as e:
        logger.error(f"خطأ في حفظ YAML: {e}")
        raise