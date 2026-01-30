from datetime import datetime
from typing import List, Tuple
from src.core.calculators.ccm_calculator import CCMCalculator
from src.core.calculators.vvm_q10_model import VVMQ10Model
from src.core.entities.temperature_reading import TemperatureReading
from src.core.enums.vvm_stage import VVMStage
from src.application.dtos.analysis_result_dto import (
    AnalysisResultDTO,
    VaccineStatus,
)
from src.core.services.rules_engine import apply_rules, RulesEngine
from src.utils.vaccine_library_loader import VaccineLibraryLoader


class EvaluateColdChainSafetyUC:
    """
    The central orchestrator for evaluating vaccine cold chain safety.
    
    This Use Case coordinates data fetching, scientific modeling (Q10/CCM),
    and decisional logic via the Rules Engine.
    
    Workflow:
        1. Fetch readings and vaccine profiles.
        2. Calculate CCM delta (Cumulative Thermal Exposure).
        3. Calculate Scientific HER (Heat Exposure Ratio) via VVMQ10Model.
        4. Apply prioritized Decision Rules.
        5. Map outcomes to DTOs and audit logs.
    """

    def __init__(self, reader, repository=None):
        """
        Initializes the Use Case with necessary drivers.
        
        Args:
            reader: The FT2 data reader.
            repository: The vaccine profile repository.
        """
        self.reader = reader
        self.repository = repository
        self.ccm_calculator = CCMCalculator()
        self.rules_engine = RulesEngine()

    def execute(self) -> List[AnalysisResultDTO]:
        """
        Executes the safety analysis for all currently active vaccines/centers.
        
        Returns:
            List[AnalysisResultDTO]: A list of detailed analysis results, 
            including decisions, VVM stages, and recommendations.
        """
        vaccines = self.reader.get_vaccines()
        readings = self.reader.read_all()

        results: List[AnalysisResultDTO] = []

        for vaccine in vaccines:
            # Enrich vaccine from library (v1.1.0)
            lib_data = VaccineLibraryLoader.get_instance().get_vaccine_data(vaccine.id)
            if lib_data:
                vaccine.category = lib_data.get('category', vaccine.category)
                vaccine.is_freeze_stable = lib_data.get('is_freeze_stable', vaccine.is_freeze_stable)
                vaccine.vvm_type = lib_data.get('vvm_type', vaccine.vvm_type)
                vaccine.actions = lib_data.get('actions', {})
                
                # Update critical limit from library if specified
                lib_temps = lib_data.get('temp_requirements', {})
                if 'max_safe' in lib_temps:
                    vaccine.full_loss_threshold_high = lib_temps['max_safe']
                
                # Thaw logic enrichment
                thaw_cfg = lib_data.get('thaw_logic', {})
                vaccine.ultra_cold_chain_required = lib_data.get('ultra_cold_chain_required', vaccine.ultra_cold_chain_required)
                vaccine.thaw_duration_days = thaw_cfg.get('thaw_duration_days', vaccine.thaw_duration_days)

            v_readings = [r for r in readings if r.vaccine_id == vaccine.id]

            if not v_readings:
                continue
            
            # Sort readings by timestamp to process them chronologically
            v_readings.sort(key=lambda r: r.recorded_at)

            # 1. CCM calculation
            ccm_result = self.ccm_calculator.calculate(v_readings)
            ccm_val = ccm_result.get("ccm_delta", 0.0)

            # 2. Q10 Model Calculation (Scientific Logic)
            model = VVMQ10Model(q10_value=vaccine.q10_value, ideal_temp=vaccine.ideal_temp)
            q10_segments = self._prepare_readings_for_q10(v_readings)
            degradation_hours = model.calculate_cumulative_degradation_hours(q10_segments)

            # 3. Calculate Heat Exposure Ratio (HER)
            shelf_life_hours = vaccine.shelf_life_days * 24
            her = degradation_hours / shelf_life_hours if shelf_life_hours > 0 else 1.0

            # 4. Use Centralized Rules Engine for Decision
            class EvaluationTarget:
                def __init__(self, v_id, readings_list, vaccine_obj):
                    self.id = v_id
                    self.critical_temp_limit = vaccine_obj.get_critical_limit()
                    self.decision = "UNKNOWN"
                    self.decision_reasons = []
                    self.vvm_stage = VVMStage.NONE
                    
                    # New stability fields (v1.1.0)
                    self.is_freeze_stable = getattr(vaccine_obj, 'is_freeze_stable', False)
                    self.actions = getattr(vaccine_obj, 'actions', {})
                    self.ultra_cold_chain_required = getattr(vaccine_obj, 'ultra_cold_chain_required', False)
                    self.thaw_start_time = getattr(vaccine_obj, 'thaw_start_time', None)
                    self.thaw_duration_days = getattr(vaccine_obj, 'thaw_duration_days', 0)

                    # Range metadata for Rule Engine (v1.1.0)
                    self.temperature_ranges = {'min': 2.0, 'max': 8.0} 
                    self.decision_thresholds = {
                        'freeze_threshold': 0.0,
                        'ccm_limit': 14400 # Default 10 days (safety margin)
                    }

                    # Rules engine needs an object with ft2_entries (with durations)
                    self.ft2_entries = []
                    for i in range(len(readings_list)):
                        reading = readings_list[i]
                        if i < len(readings_list) - 1:
                            duration = (readings_list[i+1].recorded_at - reading.recorded_at).total_seconds() / 60.0
                        else:
                            duration = 0.0
                        
                        entry = type('obj', (object,), {
                            'temperature': reading.value,
                            'duration_minutes': duration
                        })
                        self.ft2_entries.append(entry)

            target = EvaluationTarget(vaccine.id, v_readings, vaccine)
            apply_rules(target, extra_stats={
                'her': her, 
                'ccm_delta': ccm_val,
                'critical_temp_limit': vaccine.full_loss_threshold_high
            })

            # Map Rule Engine strings to VaccineStatus Enum
            status_map = {
                "REJECTED_HEAT_C": VaccineStatus.DISCARD,
                "REJECTED_FREEZE": VaccineStatus.DISCARD,
                "REJECTED_EXPIRED": VaccineStatus.DISCARD,
                "REJECTED_THAW": VaccineStatus.DISCARD,
                "ACCEPTED": VaccineStatus.SAFE,
            }
            
            base_status = status_map.get(target.decision, VaccineStatus.SAFE)
            
            # Determine Final Status
            if base_status == VaccineStatus.SAFE:
                if her > 0.5 or ccm_val > 20: status = VaccineStatus.PARTIAL
                else: status = VaccineStatus.SAFE
            else:
                status = base_status

            # --- Smart Logic & Alert System (v1.1.0) ---
            
            # 1. Thaw Tracking (Hours)
            thaw_remaining_hours = None
            is_thawing = False
            if vaccine.ultra_cold_chain_required and vaccine.thaw_start_time:
                is_thawing = True
                max_hours = vaccine.thaw_duration_days * 24
                elapsed_hours = (datetime.now() - vaccine.thaw_start_time).total_seconds() / 3600.0
                thaw_remaining_hours = max(0, max_hours - elapsed_hours)

            # 2. Determine Alert Level (Logic Matrix v1.1.0)
            if status == VaccineStatus.DISCARD or her >= 1.0:
                alert_level = "RED"
                alert_reason = f"تنبيه أحمر: تلف مؤكد (HER={her:.2f})"
            elif her >= 0.5 or is_thawing:
                alert_level = "YELLOW"
                if is_thawing:
                    alert_reason = "تنبيه أصفـر: اللقاح في مرحلة الذوبان (Thawing)"
                else:
                    alert_reason = f"تنبيه أصفر: استهلاك مرتفع للميزانية (HER={her:.2f})"
            else:
                alert_level = "GREEN"
                alert_reason = "تنبيه أخضر: اللقاح ضمن الحدود المثالية"

            result_dto = AnalysisResultDTO(
                vaccine_id=vaccine.id,
                status=status,
                her=her,
                ccm=ccm_val,
                vvm_stage=target.vvm_stage,
                alert_level=alert_level,
                category_display=vaccine.category.replace('_', ' ').title(),
                thaw_remaining_hours=thaw_remaining_hours,
                is_thawing=is_thawing,
                stability_budget_consumed_pct=min(100.0, her * 100.0)
            )
            
            # 3. Populate audit log with alert reasoning
            result_dto.add_reason(alert_reason, {"alert_level": alert_level, "her": her, "is_thawing": is_thawing})
            
            for reason in target.decision_reasons:
                result_dto.add_reason(reason)
                
            result_dto.generate_recommendations()
            results.append(result_dto)

        if self.repository:
            self.repository.save_all(results)

        return results

    def _prepare_readings_for_q10(self, readings: List[TemperatureReading]) -> List[Tuple[float, float]]:
        """
        Converts a list of TemperatureReading objects into segments of (temperature, duration_in_hours)
        """
        if len(readings) < 2:
            return []

        q10_segments = []
        for i in range(len(readings) - 1):
            start_reading = readings[i]
            end_reading = readings[i+1]
            
            duration_hours = (end_reading.recorded_at - start_reading.recorded_at).total_seconds() / 3600.0
            temp_for_segment = start_reading.value
            
            q10_segments.append((temp_for_segment, duration_hours))
            
        return q10_segments
