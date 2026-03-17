# src/infrastructure/utils/yaml_loader.py

from typing import Any

import yaml

from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


def load_yaml(file_path: str) -> Any:
    """
    تحميل ملف YAML

    Args:
        file_path: مسار ملف YAML

    Returns:
        محتوى الملف المحلل
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        logger.info("تم تحميل YAML من: %s", file_path)
        return content

    except FileNotFoundError:
        logger.error("ملف YAML غير موجود: %s", file_path)
        raise
    except yaml.YAMLError as e:
        logger.error("خطأ في تحليل YAML: %s", e)
        raise
    except Exception as e:
        logger.error("خطأ غير متوقع في تحميل YAML: %s", e)
        raise


def save_yaml(data: Any, file_path: str):
    """
    حفظ بيانات إلى ملف YAML

    Args:
        data: البيانات للحفظ
        file_path: مسار ملف YAML
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        logger.info("تم حفظ YAML إلى: %s", file_path)

    except Exception as e:
        logger.error("خطأ في حفظ YAML: %s", e)
        raise
