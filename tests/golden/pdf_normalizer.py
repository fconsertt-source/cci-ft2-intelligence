#!/usr/bin/env python3
"""
تطبيع PDF لإزالة جميع العناصر غير الحتمية قبل حساب Golden Hash
✅ يعمل على مستوى bytes
✅ يزيل timestamps, UUIDs, Object IDs, Metadata المتغيرة
"""
import hashlib
import re


def normalize_pdf_bytes(pdf_bytes: bytes) -> bytes:
    """
    إزالة جميع العناصر غير الحتمية من PDF قبل Golden hash

    Args:
        pdf_bytes: Raw PDF bytes

    Returns:
        bytes: PDF بعد التطبيع الكامل
    """
    # العمل على نص لتسهيل المعالجة (PDF يستخدم latin-1 للـ metadata)
    try:
        text = pdf_bytes.decode("latin-1", errors="ignore")
    except:
        return pdf_bytes  # Fallback إذا فشل فك الترميز

    # ========================================================================
    # 1. تطبيع Metadata timestamps
    # ========================================================================
    text = re.sub(
        r"/CreationDate\s*\([^)]+\)", "/CreationDate (D:19700101000000)", text
    )
    text = re.sub(r"/ModDate\s*\([^)]+\)", "/ModDate (D:19700101000000)", text)

    # ========================================================================
    # 2. تطبيع Metadata الأخرى المتغيرة
    # ========================================================================
    text = re.sub(r"/Producer\s*\([^)]+\)", "/Producer (Normalized)", text)
    text = re.sub(r"/Creator\s*\([^)]+\)", "/Creator (Normalized)", text)
    text = re.sub(r"/Author\s*\([^)]+\)", "/Author (Normalized)", text)
    text = re.sub(r"/Title\s*\([^)]+\)", "/Title (Normalized)", text)

    # ========================================================================
    # 3. تطبيع ID الكائنات في trailer
    # ========================================================================
    text = re.sub(r"/ID\s*\[[^\]]+\]", "/ID [(Normalized) (Normalized)]", text)

    # ========================================================================
    # 4. تطبيع timestamps المطبوعة في المحتوى
    # ========================================================================
    # YYYY-MM-DD HH:MM:SS
    text = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "1970-01-01 00:00:00", text)

    # YYYYMMDD_HHMMSS (تنسيق filename)
    text = re.sub(r"\d{8}_\d{6}", "19700101_000000", text)

    # ========================================================================
    # 5. تطبيع Reference Numbers الديناميكية
    # ========================================================================
    text = re.sub(r"CC-\d{8}-\d{6}", "CC-GOLDEN-000000", text)
    text = re.sub(r"CC-FIXED-\d{6}", "CC-GOLDEN-000000", text)
    text = re.sub(r"CC-\d{14}", "CC-GOLDEN-000000", text)

    # ========================================================================
    # 6. تطبيع UUIDs في جميع الأشكال
    # ========================================================================
    # UUID قياسي: 550e8400-e29b-41d4-a716-446655440000
    text = re.sub(
        r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
        "00000000-0000-0000-0000-000000000000",
        text,
        flags=re.I,
    )

    # UUID بدون شرطات: 550e8400e29b41d4a716446655440000
    text = re.sub(r"[a-f0-9]{32}", "00000000000000000000000000000000", text, flags=re.I)

    # UUID مختصر (8 chars): temp_dist_abc123ef
    text = re.sub(r"temp_dist_[a-f0-9]{8,}", "temp_dist_fixed", text, flags=re.I)

    # ========================================================================
    # 7. تطبيع Object IDs في هيكل PDF (اختياري - قد يكسر الهيكل)
    # ملاحظة: لا نُطبع Object IDs لأنها ضرورية لهيكل PDF
    # بدلاً من ذلك، نعتمد على أن المحتوى المطبع كافٍ لاستقرار hash
    # ========================================================================

    # ========================================================================
    # إعادة الترميز والعودة
    # ========================================================================
    try:
        return text.encode("latin-1")
    except:
        return pdf_bytes


def calculate_golden_hash(pdf_bytes: bytes) -> str:
    """
    حساب Golden Hash مستقر بعد التطبيع الكامل

    Args:
        pdf_bytes: Raw PDF bytes

    Returns:
        str: SHA256 hash مستقر
    """
    normalized = normalize_pdf_bytes(pdf_bytes)
    return hashlib.sha256(normalized).hexdigest()


def verify_hash_stability(pdf1: bytes, pdf2: bytes) -> tuple[bool, str, str]:
    """
    التحقق من استقرار Hash بين ملفين PDF

    Returns:
        tuple: (is_stable, hash1, hash2)
    """
    hash1 = calculate_golden_hash(pdf1)
    hash2 = calculate_golden_hash(pdf2)
    return (hash1 == hash2, hash1, hash2)
