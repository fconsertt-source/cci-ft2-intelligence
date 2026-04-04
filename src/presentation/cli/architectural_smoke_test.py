#!/usr/bin/env python3
"""
Architectural Smoke Test - اختبار دخان معماري
Validates Clean Architecture compliance and basic functionality.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test that all layers can be imported without circular dependencies"""
    try:
        # Domain layer
        from src.domain.entities.cooling_device import CoolingDevice
        from src.domain.entities.vaccine import Vaccine
        from src.domain.value_objects.temperature_entry import TemperatureEntry

        # Application layer
        from src.application.use_cases.generate_device_report_uc_phase2 import GenerateDeviceReportUCPhase2
        from src.application.dtos.device_report_dto import DeviceReportDTO

        # Infrastructure layer
        from src.infrastructure.repositories.device_repository import DeviceDataRepository
        from src.infrastructure.logging import get_logger

        # Shared layer
        from src.shared.config import Config

        print("✅ All layer imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_dependency_directions():
    """Test that dependencies flow inward only"""
    try:
        # Domain should not import application/infrastructure
        import src.domain.entities.cooling_device
        domain_source = inspect.getsource(src.domain.entities.cooling_device)

        if 'from src.application' in domain_source or 'from src.infrastructure' in domain_source:
            print("❌ Domain layer importing from outer layers")
            return False

        # Application should not import infrastructure (except through interfaces)
        import src.application.use_cases.generate_device_report_uc_phase2
        app_source = inspect.getsource(src.application.use_cases.generate_device_report_uc_phase2)

        if 'from src.infrastructure' in app_source and 'repository' not in app_source.lower():
            print("❌ Application layer importing infrastructure directly")
            return False

        print("✅ Dependency directions correct")
        return True
    except Exception as e:
        print(f"❌ Dependency check error: {e}")
        return False

def test_config_loading():
    """Test that configuration loads properly"""
    try:
        from src.shared.config import Config
        config = Config()
        assert hasattr(config, 'env')
        assert hasattr(config, 'data_root')
        assert hasattr(config, 'log_level')
        print("✅ Configuration loading successful")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_dto_validation():
    """Test DTO validation works"""
    try:
        from src.application.dtos.device_report_dto import DeviceReportDTO, ReportDecision, VVMStage
        from datetime import datetime

        dto = DeviceReportDTO(
            device_id="TEST_001",
            center_id="CENTER_001",
            center_name="Test Center",
            temperature_ranges={"min": 2.0, "max": 8.0},
            decision=ReportDecision.SAFE,
            vvm_stage=VVMStage.A
        )
        print("✅ DTO validation successful")
        return True
    except Exception as e:
        print(f"❌ DTO validation error: {e}")
        return False

def main():
    """Run all architectural smoke tests"""
    print("🏗️  Architectural Smoke Test")
    print("=" * 50)

    tests = [
        test_imports,
        test_dependency_directions,
        test_config_loading,
        test_dto_validation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ Architecture is sound!")
        return 0
    else:
        print("❌ Architecture issues detected!")
        return 1

if __name__ == "__main__":
    import inspect
    sys.exit(main())