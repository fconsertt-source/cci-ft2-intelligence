from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple
from shared.utils.time_utils import utc_now_datetime

@dataclass
class FileClassificationResult:
    """
    DTO: نتيجة تصنيف ملفات دفعة واحدة.
    Application Layer فقط — لا يصل لـ Domain أو Infrastructure.
    """
    run_id: str
    classified_at: datetime = field(default_factory=utc_now_datetime)

    ready_for_processing:  List[Path] = field(default_factory=list)
    already_processed:     List[Path] = field(default_factory=list)
    quarantine:            List[Tuple[Path, str, str]] = field(
        default_factory=list
    )  # (path, reason_ar, reason_en)

    @property
    def total_files(self) -> int:
        return (
            len(self.ready_for_processing)
            + len(self.already_processed)
            + len(self.quarantine)
        )

    @property
    def ssot_compliant(self) -> bool:
        """SSOT Check: لا ملفات محجورة بسبب جهاز غير مسجل. إذا False → تقرير SSOT Violation."""
        unregistered = [
            r for _, r_ar, _ in self.quarantine
            if "غير مسجل" in r_ar
        ]
        return len(unregistered) == 0

    def summary_ar(self) -> str:
        return (f"التشغيل: {self.run_id} | جاهزة: {len(self.ready_for_processing)} | "
                f"مُعالجة مسبقاً: {len(self.already_processed)} | محجورة: {len(self.quarantine)} | "
                f"SSOT: {'✅' if self.ssot_compliant else '❌'}")

    def summary_en(self) -> str:
        return (f"Run: {self.run_id} | Ready: {len(self.ready_for_processing)} | "
                f"Already processed: {len(self.already_processed)} | Quarantined: {len(self.quarantine)} | "
                f"SSOT: {'OK' if self.ssot_compliant else 'VIOLATED'}")