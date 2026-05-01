class BaseSystemException(Exception):
    """Unified root exception for system boundaries."""

    def __init__(
        self,
        user_message: str,
        code: str,
        internal_details: str | None = None,
    ):
        self.user_message = user_message
        self.code = code
        self.internal_details = internal_details
        super().__init__(user_message)


class DomainException(BaseSystemException):
    """Business rule violation."""
    pass


class ValidationException(DomainException):
    """Input validation failed."""
    pass


class NotFoundException(DomainException):
    """Requested business entity was not found."""
    pass


class InfrastructureException(BaseSystemException):
    """Failure in infrastructure dependencies."""
    pass
