# src/infrastructure/validation/default_validator.py
"""
DefaultValidator
---------------
تنفيذ بسيط للـ ValidationPort يستخدم:
* Structural validation – عبر الـ ``dict()`` للـ DTO (تأكد من قابلية التسلسل)
* Business validation – يقرأ سياسات موجودة في الخاصية ``policies`` إذا وجدت.
"""

from __future__ import annotations
from typing import Any

from src.application.exceptions import ValidationError
from src.application.ports.validation_port import ValidationPort


class DefaultValidator(ValidationPort):
    def validate(self, obj: Any) -> None:
        """
        Basic validation:
        1️⃣  إذا كان للـ obj طريقة ``dict()`` نجرب استدعاؤها – سيُرفع
            ``TypeError`` إذا لم تُنفَّذ (يعني DTO غير صالح).
        2️⃣  إذا كان للـ obj خاصية ``policies`` (قائمة من callables)
            يُستدعى كلً منها؛ يجب أن يرفع ``ValidationError`` عند الفشل.
        """
        # ---- structural -------------------------------------------------
        if hasattr(obj, "dict"):
            # استدعاء ``dict`` يضمن أن الـ DTO قابل للتسلسل
            _ = obj.dict()   # قد يرفع TypeError إذا لم يكن قابلاً للتمثيل

        # ---- business ----------------------------------------------------
        policies = getattr(obj, "policies", None)
        if policies:
            for policy in policies:
                # كل policy يجب أن تُرفع ``ValidationError`` عند الفشل
                policy()
