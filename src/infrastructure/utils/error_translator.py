from functools import wraps
import json
import yaml

from src.domain.exceptions import InfrastructureException, NotFoundException


def translate_infrastructure_errors(func):
    """Intercept infrastructure errors and translate them to system-safe exceptions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as exc:
            raise NotFoundException(
                user_message="المورد غير موجود. يرجى التحقق من إعدادات النظام.",
                code="RESOURCE_NOT_FOUND",
                internal_details=str(exc),
            ) from exc
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            raise InfrastructureException(
                user_message="فشل في قراءة بيانات النظام الأساسية. يرجى مراجعة المصدر.",
                code="INFRASTRUCTURE_DATA_PARSE_ERROR",
                internal_details=str(exc),
            ) from exc
        except Exception as exc:
            raise InfrastructureException(
                user_message="حدث خطأ في البنية التحتية. يرجى إعادة المحاولة أو التواصل مع الدعم.",
                code="INFRASTRUCTURE_FAILURE",
                internal_details=str(exc),
            ) from exc

    return wrapper
