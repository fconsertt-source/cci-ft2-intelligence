from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# HER Thresholds — عتبات الإجهاد الحراري
# ═══════════════════════════════════════════════════════════════

HER_SAFE_MAX: float = 1.0      # ≤ 1.0  → SAFE
HER_PARTIAL_MAX: float = 1.5   # ≤ 1.5  → PARTIAL
# > 1.5  → DISCARD


@dataclass(frozen=True)
class VaccineSpecification:
    """Domain value object for vaccine thermal specifications."""
    vaccine_type: str
    q10_factor: float = 2.0
    shelf_life_days: float = 730.0
    freeze_sensitive: bool = False
    vvm_type: Optional[str] = None
    min_temp: float = 2.0
    max_temp: float = 8.0
    freeze_range: Optional[tuple[float, float]] = None
    max_heat_temp: Optional[float] = None
    max_heat_duration_hours: Optional[float] = None
    regulatory_source: Optional[str] = None
    rationale: Optional[str] = None
    reference_temp_c: float = 5.0
    activation_energy_kj_mol: float = 0.0
    degradation_days_at_37C: float = 0.0
    critical_hours: float = 2.0
    excursion_time_limit: Optional[float] = None

    def __post_init__(self):
        if self.q10_factor <= 0:
            raise ValueError(f"Q10 factor must be positive, got {self.q10_factor}")
        if self.shelf_life_days <= 0:
            raise ValueError(f"Shelf life must be positive, got {self.shelf_life_days}")
        if self.activation_energy_kj_mol <= 0:
            raise ValueError(
                f"activation_energy_kj_mol must be positive, got {self.activation_energy_kj_mol}"
            )
        if self.degradation_days_at_37C <= 0:
            raise ValueError(
                f"degradation_days_at_37C must be positive, got {self.degradation_days_at_37C}"
            )

    @property
    def shelf_life_hours(self) -> float:
        """Convert shelf life to hours."""
        return self.shelf_life_days * 24.0

    @property
    def degradation_hours_at_37C(self) -> float:
        """Heat-stress reference denominator in hours for HER calculation."""
        return self.degradation_days_at_37C * 24.0


# ═══════════════════════════════════════════════════════════════
# VACCINE_CATALOGUE — كتالوج اللقاحات المركزي
# ═══════════════════════════════════════════════════════════════

VACCINE_CATALOGUE = {
    "OPV": VaccineSpecification(
        vaccine_type="OPV",
        q10_factor=3.6,
        shelf_life_days=126,
        freeze_sensitive=False,
        vvm_type="VVM2",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=(-25.0, -15.0),
        max_heat_temp=37.0,
        max_heat_duration_hours=72.0,
        regulatory_source="WHO/IVB/06.10 Table 1",
        rationale="OPV has higher Q10 factor and shorter shelf life",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=2.0,
    ),
    "HEPB": VaccineSpecification(
        vaccine_type="HEPB",
        q10_factor=2.0,
        shelf_life_days=1095,
        freeze_sensitive=True,
        vvm_type="VVM30",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=None,
        max_heat_temp=37.0,
        max_heat_duration_hours=72.0,
        regulatory_source="WHO/IVB/06.10",
        rationale="Hepatitis B is freeze-sensitive",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=7.0,
    ),
    "DTP": VaccineSpecification(
        vaccine_type="DTP",
        q10_factor=2.0,
        shelf_life_days=548,
        freeze_sensitive=True,
        vvm_type="VVM30",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=None,
        max_heat_temp=37.0,
        max_heat_duration_hours=24.0,
        regulatory_source="WHO/IVB/06.10",
        rationale="DTP is freeze-sensitive",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=14.0,
    ),
    "TT": VaccineSpecification(
        vaccine_type="TT",
        q10_factor=2.0,
        shelf_life_days=1825,
        freeze_sensitive=True,
        vvm_type="VVM30",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=None,
        max_heat_temp=37.0,
        max_heat_duration_hours=168.0,
        regulatory_source="WHO/IVB/06.10",
        rationale="Tetanus Toxoid has long heat stability",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=28.0,
    ),
    "IPV": VaccineSpecification(
        vaccine_type="IPV",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=True,
        vvm_type="VVM30",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=None,
        max_heat_temp=37.0,
        max_heat_duration_hours=24.0,
        regulatory_source="WHO/IVB/06.10",
        rationale="IPV is freeze-sensitive",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=1.0,
    ),
    "PENTA": VaccineSpecification(
        vaccine_type="PENTA",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=True,
        vvm_type="VVM30",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=None,
        max_heat_temp=37.0,
        max_heat_duration_hours=24.0,
        regulatory_source="WHO/IVB/06.10",
        rationale="Pentavalent vaccine is freeze-sensitive",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=14.0,
    ),
    "BCG": VaccineSpecification(
        vaccine_type="BCG",
        q10_factor=2.0,
        shelf_life_days=365,
        freeze_sensitive=False,
        vvm_type="VVM2",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=None,
        max_heat_temp=37.0,
        max_heat_duration_hours=168.0,
        regulatory_source="WHO/IVB/06.10",
        rationale="BCG is freeze-stable",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=28.0,
    ),
    "MEASLES": VaccineSpecification(
        vaccine_type="MEASLES",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM2",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=None,
        max_heat_temp=37.0,
        max_heat_duration_hours=168.0,
        regulatory_source="WHO/IVB/06.10",
        rationale="Measles vaccine is freeze-stable",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=7.0,
    ),
    "GENERAL": VaccineSpecification(
        vaccine_type="GENERAL",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM2",
        min_temp=2.0,
        max_temp=8.0,
        freeze_range=None,
        max_heat_temp=37.0,
        max_heat_duration_hours=24.0,
        regulatory_source="WHO/IVB/06.10",
        rationale="General vaccine specifications",
        activation_energy_kj_mol=83.144,
        degradation_days_at_37C=14.0,
    ),
}


def get_vaccine_spec(vaccine_type: str) -> Optional[VaccineSpecification]:
    """Get vaccine specification by type (case-insensitive)."""
    normalized = (vaccine_type or "GENERAL").upper().strip()
    return VACCINE_CATALOGUE.get(normalized, VACCINE_CATALOGUE.get("GENERAL"))