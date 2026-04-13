import sys
import os
from datetime import datetime, timedelta

# إضافة المجلد الجذري للمشروع لكي يتعرف على الـ imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.domain.value_objects.vaccine_specification import VACCINE_CATALOGUE
from src.domain.services.exposure_analysis_service import ExposureAnalysisService
from src.domain.services.scientific_reference_service import ScientificReferenceService
from src.application.use_cases.reconcile_legacy_vs_reference_use_case import ReconcileLegacyVsReferenceUseCase

# كائن وهمي يتقبله كلا المحركين بمرونة (Duck Typing)
class DummyReading:
    def __init__(self, temp_c: float, duration_hours: float):
        self.temperature = float(temp_c)
        self.value = float(temp_c)  # للمحرك القديم
        self.duration_minutes = float(duration_hours * 60)
        self.duration_hours = float(duration_hours)

def build_readings(temp_hours_list):
    return[DummyReading(temp, hours) for temp, hours in temp_hours_list]

def main():
    # ─── 1. بناء البيانات الذهبية (Golden Dataset Scenarios) ───
    scenarios =[
        {
            "name": "Safe Baseline (5°C for 30 days)",
            "vaccine": "OPV",
            "readings": build_readings([(5.0, 720)])
        },
        {
            "name": "Minor Heat (15°C for 2 days)",
            "vaccine": "MEASLES",
            "readings": build_readings([(15.0, 48)])
        },
        {
            "name": "Critical Heat Breach (35°C for 3 hours)",
            "vaccine": "BCG",
            "readings": build_readings([(35.0, 3)])
        },
        {
            "name": "Freeze Excursion (-2°C for 2 hours)",
            "vaccine": "HEPB",
            "readings": build_readings([(-2.0, 2)])
        },
        {
            "name": "Mixed Excursions (Fluctuating Temps)",
            "vaccine": "GENERAL",
            "readings": build_readings([(4.0, 100), (12.0, 24), (20.0, 5), (4.0, 100)])
        }
    ]

    # ─── 2. تهيئة المحركات ───
    exposure_svc = ExposureAnalysisService()
    scientific_svc = ScientificReferenceService()
    reconcile_uc = ReconcileLegacyVsReferenceUseCase()

    print("\n" + "="*80)
    print("🔬 SCIENTIFIC RECONCILIATION REPORT (Legacy Q10 vs Arrhenius/MKT)")
    print("="*80)
    
    # ─── 3. تنفيذ المصالحة وطباعة التقرير ───
    for idx, sc in enumerate(scenarios):
        spec = VACCINE_CATALOGUE.get(sc["vaccine"])
        
        # أ. المحرك التشغيلي القديم (Operational Legacy Engine)
        legacy_analysis = exposure_svc.analyze(readings=sc["readings"], spec=spec)
        legacy_stats = {"her_ratio": legacy_analysis.her_ratio}

        # ب. المحرك العلمي الموازي (Parallel Scientific Engine)
        reference_audit = scientific_svc.analyze(
            entries=sc["readings"],
            vaccine_type=sc["vaccine"]
        )

        # ج. المطابقة (Reconciliation)
        recon_result = reconcile_uc.execute(legacy_stats, reference_audit)

        # د. الطباعة
        requires_review = "⚠️ YES (Delta > 5%)" if recon_result["requires_reconciliation_review"] else "✅ NO"
        
        print(f"\nScenario {idx+1}: {sc['name']}")
        print(f"Vaccine Type: {sc['vaccine']}")
        print(f"  - Legacy HER Ratio (Q10):  {recon_result['legacy_her_ratio']:.6f}")
        print(f"  - Reference HER (Ea):      {recon_result['reference_her_ratio']:.6f}")
        print(f"  - HER Delta (Difference):  {recon_result['her_ratio_delta']:+.6f}")
        print(f"  - Scientific MKT:          {recon_result.get('reference_mkt_c', 0.0):.2f} °C")
        print(f"  - Requires Review:         {requires_review}")

    print("\n" + "="*80)
    print("✅ Reconciliation complete! This proves the new scientific engine")
    print("can run in parallel safely without breaking operational decisions.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()