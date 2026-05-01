"""
Pydantic Schema في Infrastructure فقط — لا يدخل Domain أبداً.
يُحوّل بيانات خام من CSV إلى DTOs موثوقة.
"""
from pydantic import BaseModel, field_validator, Field
from typing import Optional, Union
from datetime import datetime


class FT2EntrySchema(BaseModel):
    """
    Schema للتحقق من صحة إدخال FT2 قبل تحويله لـ DTO.
    """
    model_config = {"str_strip_whitespace": True}

    # ✅ الإصلاح: قبول datetime أو str معاً
    # FT2Parser يُخزّن datetime object رغم أن FT2EntryDTO يُعلن عنه كـ str
    # Pydantic v2 لا يُحوّل datetime → str تلقائياً، لذا يجب نقبلهما معاً
    timestamp: Union[datetime, str]

    temperature: float = Field(
        ..., ge=-30.0, le=50.0,
        description="درجة الحرارة بالسيلزيوس / Temperature in Celsius"
    )
    duration_minutes: Union[int, float] = Field(
        ..., ge=0, le=1440,
        description="مدة القراءة بالدقائق / Reading duration in minutes"
    )
    device_id: Optional[str] = Field(
        None, min_length=6
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp_format(cls, v) -> str:
        """
        يقبل datetime أو str ويُعيد دائماً ISO string.
        """
        # datetime object مباشرة من FT2Parser → حوّله لـ string
        if isinstance(v, datetime):
            return v.isoformat()

        # string → تحقق من الصيغة
        v_str = str(v).replace("Z", "+00:00")
        try:
            datetime.fromisoformat(v_str)
        except ValueError:
            raise ValueError(
                f"تنسيق الوقت غير صالح: {v} / Invalid timestamp: {v}"
            )
        return v_str

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def coerce_duration_to_int(cls, v) -> int:
        """تحويل float إلى int (مثال: 15.0 → 15)."""
        try:
            return int(float(v))
        except (TypeError, ValueError):
            raise ValueError(f"قيمة مدة غير صالحة: {v} / Invalid duration: {v}")


class FT2BatchValidator:
    """
    يُصادق على مجموعة إدخالات ويُعيد الصالح والمرفوض.
    """

    @staticmethod
    def validate_batch(
        raw_entries: list[dict]
    ) -> tuple[list, list]:
        """
        يُعيد: (valid_entries, invalid_entries_with_reasons)
        """
        valid = []
        invalid = []

        for i, entry in enumerate(raw_entries):
            try:
                validated = FT2EntrySchema(**entry)
                valid.append(validated.model_dump())
            except Exception as e:
                invalid.append({
                    "row": i,
                    "data": entry,
                    "error_ar": f"إدخال {i} غير صالح: {e}",
                    "error_en": f"Entry {i} invalid: {e}"
                })

        return valid, invalid