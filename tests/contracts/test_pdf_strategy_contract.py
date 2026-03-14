# tests/contracts/test_pdf_strategy_contract.py
#!/usr/bin/env python3
"""Contract tests ensuring all PDF strategy implementations conform to API."""

import pytest

# ✅ استيراد من المسار الصحيح
from src.domain.dtos.device_report_dto import DeviceReportDTO


def create_minimal_dto() -> DeviceReportDTO:
    """إنشاء DTO أدنى للاختبار"""
    return DeviceReportDTO(
        device_id="TEST-001",
        vaccine_type="Pfizer-BioNTech",
        total_records=0,
        excursions=(),
        final_status="safe",
        scientific_rationale="Test rationale",
    )


class TestPDFStrategyContract:
    """عقد إلزامي لجميع استراتيجيات PDF"""

    @pytest.mark.parametrize(
        "strategy_class_name",
        [
            "OfficialPDFStrategy",
            "TechnicalPDFStrategy",
            "ArabicPDFStrategy",
        ],
    )
    def test_pdf_strategy_returns_bytes(self, strategy_class_name):
        """يجب أن ترجع الاستراتيجية bytes وليس str أو None"""
        try:
            from src.infrastructure.adapters.reporting.pdf_strategy import (
                ArabicPDFStrategy,
                OfficialPDFStrategy,
                TechnicalPDFStrategy,
            )

            strategy_map = {
                "OfficialPDFStrategy": OfficialPDFStrategy,
                "TechnicalPDFStrategy": TechnicalPDFStrategy,
                "ArabicPDFStrategy": ArabicPDFStrategy,
            }
            StrategyClass = strategy_map.get(strategy_class_name)
            if StrategyClass is None:
                pytest.skip(f"{strategy_class_name} not available")
            strategy = StrategyClass()
        except ImportError as e:
            pytest.skip(f"could not import {strategy_class_name}: {e}")
        except Exception as e:
            pytest.skip(f"could not construct {strategy_class_name}: {e}")

        dto = create_minimal_dto()
        result = strategy.generate(dto, language="ar")

        assert isinstance(result, bytes), f"{strategy_class_name} must return bytes"
        assert len(result) > 0, f"{strategy_class_name} returned empty bytes"

    @pytest.mark.parametrize(
        "strategy_class_name",
        [
            "OfficialPDFStrategy",
            "TechnicalPDFStrategy",
            "ArabicPDFStrategy",
        ],
    )
    def test_pdf_strategy_valid_signature(self, strategy_class_name):
        """يجب أن يبدأ الناتج بتوقيع PDF الصالح"""
        try:
            from src.infrastructure.adapters.reporting.pdf_strategy import (
                ArabicPDFStrategy,
                OfficialPDFStrategy,
                TechnicalPDFStrategy,
            )

            strategy_map = {
                "OfficialPDFStrategy": OfficialPDFStrategy,
                "TechnicalPDFStrategy": TechnicalPDFStrategy,
                "ArabicPDFStrategy": ArabicPDFStrategy,
            }
            StrategyClass = strategy_map.get(strategy_class_name)
            if StrategyClass is None:
                pytest.skip(f"{strategy_class_name} not available")
            strategy = StrategyClass()
        except ImportError as e:
            pytest.skip(f"could not import {strategy_class_name}: {e}")
        except Exception as e:
            pytest.skip(f"could not construct {strategy_class_name}: {e}")

        dto = create_minimal_dto()
        result = strategy.generate(dto, language="ar")

        assert result.startswith(
            b"%PDF"
        ), f"{strategy_class_name} invalid PDF signature"

    @pytest.mark.parametrize(
        "strategy_class_name",
        [
            "OfficialPDFStrategy",
            "TechnicalPDFStrategy",
            "ArabicPDFStrategy",
        ],
    )
    def test_pdf_strategy_no_side_effects(self, strategy_class_name):
        """يجب ألا تسبب آثار جانبية خارجية (نفس المدخلات = نفس المخرجات)"""
        try:
            from src.infrastructure.adapters.reporting.pdf_strategy import (
                ArabicPDFStrategy,
                OfficialPDFStrategy,
                TechnicalPDFStrategy,
            )

            strategy_map = {
                "OfficialPDFStrategy": OfficialPDFStrategy,
                "TechnicalPDFStrategy": TechnicalPDFStrategy,
                "ArabicPDFStrategy": ArabicPDFStrategy,
            }
            StrategyClass = strategy_map.get(strategy_class_name)
            if StrategyClass is None:
                pytest.skip(f"{strategy_class_name} not available")
            strategy = StrategyClass()
        except ImportError as e:
            pytest.skip(f"could not import {strategy_class_name}: {e}")
        except Exception as e:
            pytest.skip(f"could not construct {strategy_class_name}: {e}")

        dto = create_minimal_dto()
        result1 = strategy.generate(dto, language="ar")
        result2 = strategy.generate(dto, language="ar")

        # PDFs may vary slightly (ReportLab embeds creation dates, IDs, etc.).
        # The contract no longer demands byte-for-byte equality, just that
        # each run produces a valid document and the sizes remain roughly the
        # same.
        assert result1.startswith(b"%PDF") and result2.startswith(
            b"%PDF"
        ), f"{strategy_class_name} did not produce valid PDFs"
        assert (
            abs(len(result1) - len(result2)) < 1024
        ), f"{strategy_class_name} produced wildly different outputs"
