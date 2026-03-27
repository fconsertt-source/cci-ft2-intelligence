#!/usr/bin/env python3
"""Debugging helpers for FT2 files (refactored to use centralized logging).

This script is intentionally small utility code used by developers and QA.
It now uses `src.infrastructure.logging.get_logger` and `FT2Parser` when parsing CSV/TSV.
"""

import os
import sys
from pathlib import Path

# Add project root to path for src imports
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.adapters.ft2_reader.parser.ft2_parser import FT2Parser
from src.infrastructure.logging import get_logger
from src.presentation.messages.message_map import MessageProvider

logger = get_logger(__name__)


def clean_bad_files():
    """حذف الملفات الفارغة أو التالفة من data/input_ft2"""
    target_dir = "data/input_ft2"
    if not os.path.exists(target_dir):
        logger.warning(MessageProvider.get('DEBUG_DIR_NOT_FOUND', path=target_dir))
        return

    logger.info(MessageProvider.get('DEBUG_CLEANING_FILES', path=target_dir))

    removed_count = 0
    for file in os.listdir(target_dir):
        if not file.endswith('.txt'):
            continue

        filepath = os.path.join(target_dir, file)
        try:
            should_remove = False
            reason = ""

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # معايير الملف التالف
            if not content.strip():
                should_remove = True
                reason = "فارغ تماماً"
            elif "Hist:" in content and "Date:" not in content:
                should_remove = True
                reason = "لا يحتوي على بيانات (فشل التحويل)"

            if should_remove:
                os.remove(filepath)
                logger.info(
                    MessageProvider.get('DEBUG_FILE_DELETED', file=file, reason=reason)
                )
                removed_count += 1

        except Exception as e:
            logger.error("❌ خطأ في فحص %s: %s", file, e)

    if removed_count == 0:
        logger.info(MessageProvider.get('DEBUG_NO_BAD_FILES'))
    else:
        logger.info(MessageProvider.get('DEBUG_CLEANED_COUNT', count=removed_count))


def debug_raw_files():
    """فحص الملفات الخام (TSV/CSV) في data/input_raw"""
    input_dir = "data/input_raw"

    if not os.path.exists(input_dir):
        logger.warning(MessageProvider.get('DEBUG_DIR_NOT_FOUND', path=input_dir))
        return

    logger.info("فحص الملفات الخام في: %s", input_dir)

    files = [f for f in os.listdir(input_dir) if f.endswith(('.tsv', '.csv'))]
    if not files:
        logger.info("لا توجد ملفات .tsv أو .csv.")
        logger.info(
            "💡 تلميح: جرب إنشاء بيانات اختبار أولاً باستخدام: python -m scripts.run_ft2_pipeline --generate-data"
        )
        return

    for file in files:
        filepath = os.path.join(input_dir, file)
        logger.info("📄 الملف: %s", file)
        logger.debug("%s", "-" * 30)

        try:
            # If CSV/TSV, try parsing using FT2Parser to get a quick health check
            entries = FT2Parser.parse_file(filepath)
            if not entries:
                logger.warning("⚠️  لم يتم استخراج إدخالات من الملف: %s", file)
                continue

            logger.info("📊 عدد الإدخالات: %d", len(entries))
            logger.info("📝 أول 3 عينات:")
            for i, e in enumerate(entries[:3]):
                logger.info(
                    "  %d: device=%s ts=%s temp=%s",
                    i + 1,
                    getattr(e, 'device_id', None),
                    getattr(e, 'timestamp', None),
                    getattr(e, 'temperature', None),
                )

        except Exception as e:
            logger.error("❌ خطأ في قراءة الملف %s: %s", file, e)


def debug_ft2_files():
    """تصحيح مشاكل ملفات FT2"""
    input_dir = "data/input_ft2"

    if not os.path.exists(input_dir):
        logger.warning(MessageProvider.get('DEBUG_DIR_NOT_FOUND', path=input_dir))
        return

    for file in os.listdir(input_dir):
        filepath = os.path.join(input_dir, file)

        if file.endswith('.txt'):
            logger.info("فحص الملف: %s", file)

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not content.strip():
                    logger.warning("⚠️  الملف فارغ تماماً: %s", file)
                else:
                    lines = content.split('\n')
                    logger.info("عدد الأسطر: %d", len(lines))
                    for i, line in enumerate(lines[:5]):
                        logger.debug("سطر %d: %s", i + 1, line[:100])

                    # البحث عن كلمات مفتاحية
                    keywords = ['Hist:', 'Date:', 'Min T:', 'Serial:']
                    for kw in keywords:
                        if kw in content:
                            logger.info("✅ وجد: %s", kw)
                        else:
                            logger.info("❌ لم يجد: %s", kw)
            except Exception as e:
                logger.error("❌ خطأ في فحص %s: %s", file, e)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clean_bad_files()
    else:
        debug_raw_files()
        debug_ft2_files()
        logger.info(MessageProvider.get('DEBUG_CLEAN_HINT'))
