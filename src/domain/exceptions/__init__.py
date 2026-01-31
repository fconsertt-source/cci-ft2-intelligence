class DomainException(Exception):
    """Base class for domain-level exceptions."""


class ValidationException(DomainException):
    pass


class NotFoundException(DomainException):
    pass


class InfrastructureException(Exception):
    """Represents failures in Infrastructure boundary."""
    pass
