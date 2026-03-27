# src/domain/value_objects/vaccine_specification.py
"""
VaccineSpecification — مواصفات اللقاح العلمية
المصدر: WHO/IVB/06.10 + WHO/PQS/E06/IN02.1

قيمة ثابتة (frozen) — لا تتغير بعد الإنشاء.
تُستخدم كمدخل لـ Q10HerCalculator و ExposureAnalysisService.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ──────────────────────────────────────────────────────────────
# ثوابت WHO/IVB/06.10 — عتبات CCM الرسمية
# المصدر: WHO/PQS/E06/IN02.1 § 4.2.3
# ──────────────────────────────────────────────────────────────
CCM_WINDOW_A_DAYS_AT_12C: float = 3.0  # نافذة A عند 12°C
CCM_WINDOW_AB_DAYS_AT_12C: float = 8.0  # نافذة A+B عند 12°C
CCM_WINDOW_ABC_DAYS_AT_12C: float = 14.0  # نافذة A+B+C عند 12°C
CCM_CRITICAL_TEMP: float = 34.0  # عتبة النافذة D
CCM_CRITICAL_HOURS: float = 2.0  # ساعتان فوق 34°C = DISCARD

# عتبة HER للقرار (مستنبطة من VVM reaction rates — Table 1 WHO/IVB/06.10)
HER_SAFE_MAX: float = 1.0
HER_PARTIAL_MAX: float = 1.5


@dataclass(frozen=True)
class VaccineSpecification:
    """
    المواصفات العلمية للقاح — مصدر الحقيقة للحسابات الحرارية.

    Attributes:
        vaccine_type:       رمز نوع اللقاح (OPV, HEPB, DTP, ...)
        q10_factor:         معامل Q10 (افتراضي 2.0 وفق Arrhenius)
        shelf_life_days:    العمر الافتراضي للقاح عند درجة المرجع (5°C)
        reference_temp_c:   درجة الحرارة المرجعية للحساب (افتراضي 5.0°C)
        freeze_sensitive:   هل يتلف عند التجمد؟ (لقاحات الألومنيوم)
        vvm_type:           نوع مؤشر VVM (VVM2/7/14/30)
        critical_temp_c:    درجة الخطر الفوري (افتراضي 34.0°C)
        critical_hours:     مدة الخطر الفوري بالساعات (افتراضي 2.0)
        rationale:          مبرر علمي للمواصفات
    """

    vaccine_type: str
    q10_factor: float = 2.0
    shelf_life_days: float = 730.0  # سنتان افتراضياً
    reference_temp_c: float = 5.0
    freeze_sensitive: bool = False
    vvm_type: Optional[str] = None  # VVM2 / VVM7 / VVM14 / VVM30
    critical_temp_c: float = CCM_CRITICAL_TEMP
    critical_hours: float = CCM_CRITICAL_HOURS
    rationale: str = ""
    # ── حقول التوافق الرجعي (legacy) ─────────────────────────
    # محفوظة لمنع كسر الكود القديم — لا تُستخدم في حسابات A1-A4
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    excursion_time_limit: Optional[float] = None
    freeze_range: Optional[tuple] = None
    max_heat_temp: Optional[float] = None
    max_heat_duration_hours: Optional[float] = None
    regulatory_source: Optional[str] = None

    def __post_init__(self) -> None:
        if self.q10_factor <= 0:
            raise ValueError(f"q10_factor must be > 0, got {self.q10_factor}")
        if self.shelf_life_days <= 0:
            raise ValueError(f"shelf_life_days must be > 0, got {self.shelf_life_days}")

    @property
    def shelf_life_hours(self) -> float:
        """العمر الافتراضي بالساعات — مُستخدم في حساب HER ratio."""
        return self.shelf_life_days * 24.0


# ──────────────────────────────────────────────────────────────
# كتالوج اللقاحات الافتراضي — مصدر: WHO/IVB/06.10 Table 9
# ──────────────────────────────────────────────────────────────
VACCINE_CATALOGUE: dict[str, VaccineSpecification] = {
    "OPV": VaccineSpecification(
        vaccine_type="OPV",
        q10_factor=3.6,
        shelf_life_days=126,
        freeze_sensitive=False,
        vvm_type="VVM2",
        rationale="الأكثر حساسية للحرارة — VVM2 ينتهي بعد يومين عند 37°C",
    ),
    "HEPB": VaccineSpecification(
        vaccine_type="HEPB",
        q10_factor=2.0,
        shelf_life_days=1460,  # 4 سنوات
        freeze_sensitive=True,
        vvm_type="VVM30",
        rationale="مستقر حرارياً — حساس للتجمد (ألومنيوم). VVM30",
    ),
    "DTP": VaccineSpecification(
        vaccine_type="DTP",
        q10_factor=2.0,
        shelf_life_days=548,  # 18 شهراً
        freeze_sensitive=True,
        vvm_type="VVM14",
        rationale="العامل المحدِّد: مكوّن السعال الديكي. حساس للتجمد",
    ),
    "DT": VaccineSpecification(
        vaccine_type="DT",
        q10_factor=2.0,
        shelf_life_days=1095,  # 3 سنوات
        freeze_sensitive=True,
        vvm_type="VVM30",
        rationale="سُمِّيات ديفتريا وكُزاز — مستقرة. حساسة للتجمد",
    ),
    "TT": VaccineSpecification(
        vaccine_type="TT",
        q10_factor=2.0,
        shelf_life_days=1095,
        freeze_sensitive=True,
        vvm_type="VVM30",
        rationale="سُمّ الكُزاز — مستقر للغاية. حساس للتجمد",
    ),
    "TD": VaccineSpecification(
        vaccine_type="TD",
        q10_factor=2.0,
        shelf_life_days=1095,
        freeze_sensitive=True,
        vvm_type="VVM30",
        rationale="سُمِّيات كُزاز وديفتريا (جرعة مخفضة). حساسة للتجمد",
    ),
    "BCG": VaccineSpecification(
        vaccine_type="BCG",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM14",
        rationale="مجفف — يتحمل التجمد. يفقد الفاعلية بالحرارة تدريجياً",
    ),
    "MEASLES": VaccineSpecification(
        vaccine_type="MEASLES",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM7",
        rationale="مجفف — مستقر نسبياً. يتحمل التجمد",
    ),
    "MMR": VaccineSpecification(
        vaccine_type="MMR",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM7",
        rationale="مزيج ثلاثي مجفف — المكوّن الأضعف يحدد VVM7",
    ),
    "YF": VaccineSpecification(
        vaccine_type="YF",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type="VVM7",
        rationale="حمى صفراء مجففة — يفقد الفاعلية سريعاً بعد إعادة التركيب",
    ),
    "IPV": VaccineSpecification(
        vaccine_type="IPV",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=True,
        vvm_type="VVM14",
        rationale="شلل الأطفال المعطّل — حساس للتجمد وللحرارة",
    ),
    # افتراضي عام عند عدم معرفة النوع
    "GENERAL": VaccineSpecification(
        vaccine_type="GENERAL",
        q10_factor=2.0,
        shelf_life_days=730,
        freeze_sensitive=False,
        vvm_type=None,
        rationale="مواصفة افتراضية عامة — استخدم عند غياب بيانات النوع",
    ),
}


def get_vaccine_spec(vaccine_type: str) -> VaccineSpecification:
    """
    جلب مواصفات اللقاح من الكتالوج.
    يعود للمواصفة الافتراضية عند غياب النوع.
    """
    normalized = vaccine_type.upper().strip() if vaccine_type else "GENERAL"
    return VACCINE_CATALOGUE.get(normalized, VACCINE_CATALOGUE["GENERAL"])
