from typing import Protocol

class FeatureFlagPort(Protocol):
    """واجهة للتحكم في الميزات (Feature Flags) – Domain لا يعرف التنفيذ."""
    def is_enabled(self, flag_name: str) -> bool:
        """إرجاع True إذا كانت الميزة مفعلة."""
        ...
