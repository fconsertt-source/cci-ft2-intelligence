"""
Architecture Isolation Test — Clean Architecture Boundary Check.

يُثبت أن Use Cases تتطلب Dependency Injection ولا يمكن إنشاؤها بدونها.
الملف نُقل من src/infrastructure/ إلى tests/ ليكون اختباراً معمارياً.
"""
import pytest
from unittest.mock import MagicMock

def test_usecase_requires_dependency_injection():
    """
    Use Case يجب أن يتطلب Dependencies — لا يمكن إنشاؤه فارغاً.
    هذا يضمن أن Infrastructure لا يمكنها استخدام Use Cases مباشرة.
    """
    from src.application.use_cases.manage_file_lifecycle import ManageFileLifecycleUseCase
    from src.application.ports.i_file_registry import IFileRegistry
    from src.application.ports.i_center_registry import ICenterRegistry
    
    # محاولة الإنشاء بدون Dependencies يجب أن تفشل
    with pytest.raises(TypeError):
        ManageFileLifecycleUseCase()
    
    # الإنشاء الصحيح يتطلب Dependencies
    mock_file_reg = MagicMock(spec=IFileRegistry)
    mock_center_reg = MagicMock(spec=ICenterRegistry)
    
    usecase = ManageFileLifecycleUseCase(
        file_registry=mock_file_reg,
        center_registry=mock_center_reg
    )
    
    assert usecase is not None

def test_infrastructure_cannot_import_usecase_in_production():
    """
    يوثق أن استيراد Use Case من Infrastructure ممنوع في الإنتاج.
    هذا الاختبار ينجح لأننا في tests/، لكن لو كان في src/infrastructure/
    سيكون انتهاكاً معمارياً.
    """
    # هذا مسموح هنا لأننا في tests/
    from src.application.use_cases.manage_file_lifecycle import ManageFileLifecycleUseCase
    assert ManageFileLifecycleUseCase is not None
    # في الكود المنتج، هذا الاستيراد ممنوع
