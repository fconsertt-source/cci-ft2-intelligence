"""
YAML-based implementation of VaccineSpecificationPort.
Reads vaccine specifications from config/vaccine_library.yaml.

الإصدار: 2.0
تاريخ التحديث: 22 مارس 2026
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

import yaml

from src.application.ports.vaccine_specification_port import \
    VaccineSpecificationPort
from src.domain.value_objects.vaccine_specification import VaccineSpecification

logger = logging.getLogger(__name__)


class JsonVaccineSpecRepository(VaccineSpecificationPort):
    """
    YAML-based implementation of VaccineSpecificationPort.

    سياسة السلامة:
    - الإنتاج: تحميل من vaccine_library.yaml
    - الطوارئ: Fallback لـ 3 لقاحات فقط (ليس للإنتاج)
    """

    # Fallback للطوارئ فقط — 3 لقاحات
    _MINIMAL_FALLBACK: Dict[str, VaccineSpecification] = {
        "GENERAL": VaccineSpecification(
            vaccine_type="GENERAL",
            q10_factor=2.0,
            shelf_life_days=730,
            freeze_sensitive=False,
            vvm_type="VVM2",
            ccm_limit=600,
            reference_temp_c=5.0,
            critical_temp_c=34.0,
            critical_hours=2.0,
            name_ar="لقاح عام (للطوارئ)",
        ),
        "OPV": VaccineSpecification(
            vaccine_type="OPV",
            q10_factor=3.6,
            shelf_life_days=126,
            freeze_sensitive=False,
            vvm_type="VVM2",
            ccm_limit=300,
            reference_temp_c=5.0,
            critical_temp_c=34.0,
            critical_hours=2.0,
            name_ar="شلل الأطفال الفموي (للطوارئ)",
        ),
        "HEPB": VaccineSpecification(
            vaccine_type="HEPB",
            q10_factor=2.0,
            shelf_life_days=1095,
            freeze_sensitive=True,
            vvm_type="VVM30",
            ccm_limit=500,
            reference_temp_c=5.0,
            critical_temp_c=34.0,
            critical_hours=2.0,
            name_ar="التهاب الكبد B (للطوارئ)",
        ),
    }

    def __init__(self, yaml_path: Optional[Path] = None):
        if yaml_path is None:
            yaml_path = Path("config/vaccine_library.yaml")
        self._yaml_path = yaml_path
        self._specs = self._load_specs()

    def _load_specs(self) -> Dict[str, VaccineSpecification]:
        """تحميل مواصفات اللقاحات من YAML."""
        if not self._yaml_path.exists():
            logger.warning(f"vaccine_library.yaml not found at {self._yaml_path}")
            return self._MINIMAL_FALLBACK.copy()

        try:
            with open(self._yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "vaccines" not in data:
                raise ValueError("Invalid YAML: missing 'vaccines' key")

            specs = {}
            for vaccine_type, spec_data in data["vaccines"].items():
                specs[vaccine_type] = VaccineSpecification(
                    vaccine_type=vaccine_type,
                    q10_factor=spec_data.get("q10_factor", 2.0),
                    shelf_life_days=spec_data.get("shelf_life_days", 730),
                    freeze_sensitive=spec_data.get("freeze_sensitive", False),
                    vvm_type=spec_data.get("vvm_type", "VVM2"),
                    ccm_limit=spec_data.get("ccm_limit", 600),
                    reference_temp_c=spec_data.get("reference_temp_c", 5.0),
                    critical_temp_c=spec_data.get("critical_temp_c", 34.0),
                    critical_hours=spec_data.get("critical_hours", 2.0),
                    name_ar=spec_data.get("name_ar"),
                    name_en=spec_data.get("name_en"),
                    storage=spec_data.get("storage"),
                    heat_stability=spec_data.get("heat_stability"),
                    opened_vial_h=spec_data.get("opened_vial_h"),
                    protect_light=spec_data.get("protect_light", False),
                    shake_test=spec_data.get("shake_test", False),
                    ectc_approved=spec_data.get("ectc_approved", False),
                    ectc_max_temp_c=spec_data.get("ectc_max_temp_c"),
                    ectc_max_days=spec_data.get("ectc_max_days"),
                    storage_special=spec_data.get("storage_special"),
                    note=spec_data.get("note"),
                    who_code=spec_data.get("who_code"),
                )

            if not specs:
                raise ValueError("No vaccines loaded from YAML")

            logger.info(f"Loaded {len(specs)} vaccines from vaccine_library.yaml")
            return specs

        except Exception as e:
            logger.error(f"Failed to load vaccine_library.yaml: {e}")
            return self._MINIMAL_FALLBACK.copy()

    def get_spec(self, vaccine_type: str) -> Optional[VaccineSpecification]:
        return self._specs.get(vaccine_type.upper())

    def get_all_specs(self) -> Dict[str, VaccineSpecification]:
        return self._specs.copy()

    def reload(self) -> None:
        """إعادة التحميل من YAML (للتحديثات الديناميكية)."""
        self._specs = self._load_specs()

    def get_source_info(self) -> Dict:
        """معلومات عن مصدر البيانات."""
        return {
            "source": "YAML" if self._yaml_path.exists() else "FALLBACK",
            "yaml_path": str(self._yaml_path),
            "vaccine_count": len(self._specs),
            "is_production_ready": self._yaml_path.exists() and len(self._specs) >= 10,
        }
