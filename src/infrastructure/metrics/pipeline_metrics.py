from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict
import logging

@dataclass
class PipelineRunMetrics:
    """
    سجل قابل للقياس لكل تشغيل Pipeline.
    """
    run_id: str
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime = None

    # SSOT Metrics
    yaml_centers_count:   int = 0
    affected_centers_count: int = 0
    shadow_centers:       List[str] = field(default_factory=list)

    # Data Lifecycle Metrics
    total_input_files:    int = 0
    ready_files:          int = 0
    already_processed:    int = 0
    quarantined_files:    int = 0

    # Data Quality Metrics
    total_entries:        int = 0
    valid_entries:        int = 0
    rejected_entries:     int = 0

    # Performance Metrics
    stage_latencies: Dict[str, float] = field(default_factory=dict)

    @property
    def ssot_compliant(self) -> bool:
        return self.yaml_centers_count == self.affected_centers_count

    @property
    def data_quality_score(self) -> float:
        if self.total_entries == 0:
            return 0.0
        return round(self.valid_entries / self.total_entries, 4)

    @property
    def total_run_seconds(self) -> float:
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds()
        return 0.0

    def to_prometheus_format(self) -> str:
        lines = [
            f"cci_ssot_yaml_centers {self.yaml_centers_count}",
            f"cci_ssot_affected_centers {self.affected_centers_count}",
            f"cci_ssot_compliant {1 if self.ssot_compliant else 0}",
            f"cci_data_quality_score {self.data_quality_score}",
            f"cci_quarantine_files_total {self.quarantined_files}",
            f"cci_pipeline_run_seconds {self.total_run_seconds}",
        ]
        return "\n".join(lines)

    def print_bilingual_summary(self, logger: logging.Logger) -> None:
        separator = "=" * 70
        logger.info(separator)
        logger.info("ملخص تشغيل خط المعالجة / Pipeline Run Summary")
        logger.info(separator)
        logger.info(
            "SSOT: %s | يانغ/YAML: %d | متأثرة/Affected: %d",
            "✅" if self.ssot_compliant else "❌",
            self.yaml_centers_count,
            self.affected_centers_count
        )
        logger.info(
            "الملفات / Files: إجمالي %d | جاهزة %d | مكررة %d | محجورة %d",
            self.total_input_files, self.ready_files,
            self.already_processed, self.quarantined_files
        )
        logger.info(
            "جودة البيانات / Data Quality: %.1f%% (%d/%d إدخال صالح)",
            self.data_quality_score * 100,
            self.valid_entries, self.total_entries
        )
        if self.finished_at:
            logger.info("الزمن الإجمالي / Total Time: %.2f ثانية/sec", self.total_run_seconds)
        logger.info(separator)