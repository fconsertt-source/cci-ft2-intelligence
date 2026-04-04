from typing import List, FrozenSet, Tuple

class CenterImpactService:
    """
    Service: حساب المراكز المتأثرة بشكل صحيح.
    يُصلح الخلل في run_ft2_pipeline.py (8 بدلاً من 5).
    """

    @staticmethod
    def count_affected_centers(centers: list) -> int:
        """
        يحسب عدد المراكز الفريدة التي تحتوي بيانات.
        يجب أن يساوي عدد مراكز YAML دائماً (SSOT).
        """
        return len({
            c.id
            for c in centers
            if any(
                len(u.ft2_entries) > 0
                for u in c.equipment_units
            )
        })

    @staticmethod
    def verify_ssot(
        yaml_center_count: int,
        affected_center_count: int
    ) -> Tuple[bool, str]:
        """
        SSOT Verification: يتحقق من تطابق الأعداد.
        يُعيد (is_valid, message_ar/en).
        """
        if yaml_center_count == affected_center_count:
            return True, (
                f"✅ SSOT محفوظ: {yaml_center_count} مراكز / "
                f"SSOT OK: {yaml_center_count} centers"
            )

        diff = affected_center_count - yaml_center_count
        return False, (
            f"❌ SSOT مكسور: {yaml_center_count} YAML "
            f"≠ {affected_center_count} متأثرة "
            f"({diff:+d} مراكز غير متوقعة) / "
            f"SSOT VIOLATED: {diff:+d} unexpected centers"
        )

    @staticmethod
    def get_unregistered_centers(
        centers: list,
        yaml_ids: FrozenSet[str]
    ) -> list:
        """كشف المراكز في البيانات غير الموجودة في YAML"""
        return [
            c for c in centers
            if c.id not in yaml_ids
        ]