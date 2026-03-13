# PATCH — src/domain/services/rules_engine.py
# التغيير الوحيد: VVMStageRule تقرأ "her_ratio" بدلاً من "her"
# ---------------------------------------------------------------
# السطر القديم:
#     her = stats.get("her", 0.0)
#
# السطر الجديد:
#     her = stats.get("her_ratio", stats.get("her", 0.0))
#
# نستخدم fallback على "her" للتوافق مع الاختبارات القديمة.
# ---------------------------------------------------------------

# class VVMStageRule(DecisionRule):
#     def evaluate(self, center, stats: Dict[str, Any]) -> Optional[str]:
#
#         # ← التغيير هنا فقط
#         her = stats.get("her_ratio", stats.get("her", 0.0))
#
#         if her >= 1.0:
#             center.vvm_stage = VVMStage.D
#             center.decision_reasons.append(
#                 "VVM المرحلة D: اللقاح منتهي الصلاحية حرارياً"
#             )
#             return "REJECTED_HEAT_C"
#         elif her >= 0.7:
#             center.vvm_stage = VVMStage.C
#             center.decision_reasons.append(
#                 "VVM المرحلة C: اقتراب شديد من نهاية الصلاحية"
#             )
#         elif her >= 0.4:
#             center.vvm_stage = VVMStage.B
#             center.decision_reasons.append("VVM المرحلة B: تدهور ملحوظ")
#         elif her >= 0.1:
#             center.vvm_stage = VVMStage.A
#             center.decision_reasons.append("VVM المرحلة A: بداية تأثر بالحرارة")
#         else:
#             center.vvm_stage = VVMStage.NONE
#
#         return None
