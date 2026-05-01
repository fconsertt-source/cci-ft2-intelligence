from pathlib import Path
import re

class DeviceIDExtractor:
    """
    Domain Service: استخراج Device ID من اسم الملف.

    القاعدة الواحدة: كل device_id في النظام يمر من هنا.
    لا استخراج في أي ملف آخر (Single Source of Logic).

    أنماط الملفات المدعومة:
    - 130600112663_202603251042.txt  → 130600112663
    - safe_hospital_130600112764.csv → 130600112764
    - freeze_clinic_130600112767.csv → 130600112767
    """

    # النمط الأساسي: 12 رقماً تبدأ بـ 130600
    DEVICE_ID_PATTERN = re.compile(r'((?:1306|1606)\d{8})')

    @classmethod
    def extract(cls, filename: str) -> str:
        """يستخرج device_id من اسم الملف. يرفع ValueError إذا لم يجد النمط."""
        stem = Path(filename).stem
        match = cls.DEVICE_ID_PATTERN.search(stem)

        if not match:
            raise ValueError(f"لا يمكن استخراج device_id من: {filename}. النمط المتوقع: 12 رقماً تبدأ بـ 1306")

        return match.group(1)

    @classmethod
    def is_valid_device_id(cls, device_id: str) -> bool:
        return bool(re.fullmatch(r'1306\d{8}', device_id))