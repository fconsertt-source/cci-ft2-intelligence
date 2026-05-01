import shutil
import logging
from pathlib import Path
from src.shared.utils.time_utils import utc_now_datetime

logger = logging.getLogger(__name__)

class FileArchiver:
    """
    Infrastructure: النقل الفيزيائي للملفات فقط.

    المسؤولية الواحدة: ينقل الملفات بين المجلدات.
    لا يحسب Hash، لا يتحقق من صحة البيانات، لا يقرر.
    Application تقرر متى — Infrastructure تنفّذ كيف.
    """

    def __init__(self, base_data_path: Path):
        self._archive_dir = base_data_path / "archive"
        self._quarantine_dir = base_data_path / "staging" / "quarantine"

        self._archive_dir.mkdir(parents=True, exist_ok=True)
        self._quarantine_dir.mkdir(parents=True, exist_ok=True)

    def archive_processed_file(
        self,
        source: Path,
        run_id: str
    ) -> Path:
        """
        ينقل الملف من input_raw/ إلى archive/{run_id}/
        يُفرغ input_raw/ بعد كل تشغيل ناجح.
        """
        dest_dir = self._archive_dir / run_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest = dest_dir / source.name

        if dest.exists():
            # ملف بنفس الاسم موجود — أضف timestamp
            timestamp = utc_now_datetime().strftime("%H%M%S")
            dest = dest_dir / f"{source.stem}_{timestamp}{source.suffix}"

        shutil.move(str(source), str(dest))
        logger.info(
            "تمت الأرشفة / Archived: %s → %s",
            source.name, dest.relative_to(self._archive_dir)
        )
        return dest

    def quarantine_file(
        self,
        source: Path,
        reason_ar: str,
        reason_en: str
    ) -> Path:
        """
        ينقل الملف للحجر الصحي مع توثيق سبب الرفض.
        يُنشئ ملف .rejection.txt بجانب الملف المحجور.
        """
        dest = self._quarantine_dir / source.name

        if dest.exists():
            timestamp = utc_now_datetime().strftime("%Y%m%d_%H%M%S")
            dest = self._quarantine_dir / f"{source.stem}_{timestamp}{source.suffix}"

        shutil.move(str(source), str(dest))

        # توثيق سبب الرفض
        rejection_log = dest.with_suffix(".rejection.txt")
        rejection_log.write_text(
            f"السبب (AR): {reason_ar}\n"
            f"Reason (EN): {reason_en}\n"
            f"الوقت / Time: {utc_now_datetime().isoformat()}\n"
            f"الملف / File: {source.name}\n",
            encoding="utf-8"
        )
        logger.warning("تم الحجر / Quarantined: %s | السبب: %s", source.name, reason_ar)
        return dest

    def cleanup_input_raw(self, input_raw_dir: Path) -> int:
        """
        يُفرغ input_raw/ من الملفات المتبقية بعد التشغيل.
        يُعيد عدد الملفات المحذوفة.
        تُستدعى فقط بعد نجاح Pipeline الكامل.
        """
        removed = 0
        for f in input_raw_dir.glob("*.csv"):
            f.unlink()
            removed += 1

        logger.info("تم تفريغ input_raw/ / Cleaned input_raw: %d ملف", removed)
        return removed