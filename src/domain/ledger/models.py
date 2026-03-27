from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, fields, replace
from datetime import datetime, timezone
from typing import Optional

from src.domain.enums.ledger_event import LedgerEvent


@dataclass(frozen=True)
class LedgerEntry:
    """
    مدخلة سجل جنائي محصّنة بسلسلة Hash.

    Domain Model نقي - لا يحتوي على أي logic خاص بالـ Infrastructure.
    """

    event_id: str
    event_type: LedgerEvent
    timestamp: str
    file_hash: str

    ft2_serial: Optional[str] = None
    asset_id: Optional[str] = None
    authenticity_status: Optional[str] = None
    thermal_status: Optional[str] = None
    alarm_detected: Optional[bool] = None
    source_path: Optional[str] = None
    destination_path: Optional[str] = None

    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None
    signature: Optional[str] = None

    def _to_serializable_dict(self, include_current_hash: bool = False) -> dict:
        """
        تحويل المدخلة إلى قاموس من الأنواع البدائية فقط.

        ✅ حاسم: event_type.name يعيد "FILE_INGESTED" وليس LedgerEvent object
        ✅ حاسم: previous_hash لا يُحذف حتى لو كان None
        """
        data = {
            "event_id": self.event_id,
            # store the lowercase snake_case value so the ledger is
            # human-readable and matches translated keys.
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "file_hash": self.file_hash,
            "ft2_serial": self.ft2_serial,
            "asset_id": self.asset_id,
            "authenticity_status": self.authenticity_status,
            "thermal_status": self.thermal_status,
            "alarm_detected": self.alarm_detected,
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "previous_hash": self.previous_hash,  # ✅ لا يُحذف حتى لو None
        }

        if include_current_hash:
            data["current_hash"] = self.current_hash
            data["signature"] = self.signature

        # ✅ نستبعد القيم None فقط (ما عدا previous_hash)
        return {k: v for k, v in data.items() if v is not None or k == "previous_hash"}

    def to_canonical_json(self) -> str:
        """
        تحويل المدخلة إلى JSON قياسي لحساب hash ثابت.

        القواعد الجنائية:
        1. مفاتيح مرتبة (sort_keys=True)
        2. بدون مسافات زائدة (separators=(',', ':'))
        3. أنواع بدائية فقط (no Enum, no datetime, no bytes)
        4. استبعاد الحقول المحسوبة (current_hash, signature)
        """
        data_for_hash = self._to_serializable_dict()
        data_for_hash.pop("current_hash", None)
        data_for_hash.pop("signature", None)

        return json.dumps(
            data_for_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    def compute_hash(self) -> str:
        """
        حساب SHA-256 للمدخلة بصيغة قياسية.

        ✅ محددة تماماً: نفس الكائن يعيد نفس hash دائماً
        ✅ لا تقبل أي parameters خارجية
        """
        canonical = self.to_canonical_json()
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def with_computed_hash(self, previous_hash: Optional[str] = None) -> LedgerEntry:
        """
        إنشاء نسخة من المدخلة مع ربطها بالسلسلة وحساب الـ Hash النهائي.

        ✅ التصحيح الحاسم: نضمن أن previous_hash يُحفظ بشكل دائم في entry النهائي
        """
        # 1. إنشاء نسخة مؤقتة مع previous_hash الجديد
        temp_entry = replace(self, previous_hash=previous_hash, current_hash=None)

        # 2. حساب الـ Hash على temp_entry (الذي يحتوي previous_hash الصحيح)
        computed_hash = temp_entry.compute_hash()

        # 3. إنشاء entry نهائي مع hash المحسوب
        return replace(temp_entry, current_hash=computed_hash)

    def verify_chain(self, previous_hash: Optional[str]) -> bool:
        """
        التحقق من سلامة ربط السلسلة.

        ✅ التصحيح: اسم المعامل previous_hash ليطابق الاختبارات
        """
        if self.previous_hash != previous_hash:
            return False
        if self.current_hash != self.compute_hash():
            return False
        return True

    @classmethod
    def from_dict(cls, data: dict) -> LedgerEntry:
        """
        إعادة بناء LedgerEntry من قاموس (عند القراءة من ledger).

        ✅ التصحيح: اسم المعامل 'data' وليس 'dict'
        ✅ يحول event_type من string إلى LedgerEvent enum
        ✅ يتعامل مع الحقول الديناميكية بشكل آمن
        """
        filtered_data = data.copy()  # ✅ الآن data معرّف

        # تحويل event_type من string إلى enum
        if isinstance(filtered_data.get("event_type"), str):
            val = filtered_data.get("event_type")
            # first try converting by value (preferred)
            try:
                filtered_data["event_type"] = LedgerEvent(val)
            except ValueError:
                # fallback to converting by name for legacy entries
                try:
                    filtered_data["event_type"] = LedgerEvent[val]
                except KeyError:
                    raise ValueError(f"Invalid event_type: {val}")

        # تصفية الحقول لتناسب constructor
        constructor_fields = {f.name for f in fields(cls) if f.init}
        return cls(
            **{k: v for k, v in filtered_data.items() if k in constructor_fields}
        )


@dataclass
class LedgerChainState:
    """حالة السلسلة الحالية"""

    last_entry_hash: Optional[str] = None
    entry_count: int = 0
    last_updated: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        from dataclasses import asdict

        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> LedgerChainState:
        """
        ✅ التصحيح: اسم المعامل 'data' وليس 'dict'
        """
        return cls(**data)  # ✅ الآن data معرّف
