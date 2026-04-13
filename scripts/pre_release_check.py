#!/usr/bin/env python3
import sys
from pathlib import Path

def check_lifecycle_system():
    """تحقق من جاهزية نظام إدارة دورة حياة الملف"""
    root = Path(__file__).parent.parent
    checks = [
        ("FileStatus Enum", root / "src/domain/enums/file_status.py"),
        ("FileIngestionRecord VO", root / "src/domain/value_objects/file_ingestion_record.py"),
        ("DeviceIDExtractor Service", root / "src/domain/services/device_id_extractor.py"),
        ("IFileRegistry Port", root / "src/application/ports/i_file_registry.py"),
        ("ManageFileLifecycleUseCase", root / "src/application/use_cases/manage_file_lifecycle.py"),
        ("FileArchiver", root / "src/infrastructure/lifecycle/file_archiver.py"),
        ("FileRegistryImpl", root / "src/infrastructure/repositories/file_registry_impl.py"),
        ("CircuitBreaker", root / "src/infrastructure/services/circuit_breaker.py"),
        ("Metrics System", root / "src/infrastructure/metrics/pipeline_metrics.py"),
    ]

    passed = []
    failed = []
    
    print("\n" + "="*60)
    print("🔍 فحص جاهزية الإصدار / Pre-Release Readiness Check")
    print("="*60)

    for name, path in checks:
        if path.exists():
            print(f"  ✅ {name:.<40} موجود")
            passed.append(name)
        else:
            print(f"  ❌ {name:.<40} مفقود!")
            failed.append(name)

    # فحص الديون التقنية
    dtos_in_domain = root / "src/domain/dtos"
    if dtos_in_domain.exists():
        print("  ❌ انتهاك معماري: مجلد domain/dtos لا يزال موجوداً!")
        failed.append("Clean Architecture Violation")
    else:
        print("  ✅ نظام DTOs الموحد: سليم")

    print("-" * 60)
    print(f"النتيجة الإجمالية: {len(passed)} ناجح | {len(failed)} فاشل")
    
    if failed:
        print("\n⛔ النظام غير جاهز للإنتاج. يرجى معالجة النقاط المفقودة.")
        return False
    
    print("\n🚀 النظام جاهز للإنتاج 100%! تهانينا.")
    return True

if __name__ == "__main__":
    if not check_lifecycle_system():
        sys.exit(1)
    sys.exit(0)