"""Application mappers package.

Place to add mapping utilities that convert Domain entities to DTOs and vice versa.
Initially empty — use concrete mapper modules here when migrating mapping logic.
"""


from .exposure_mapper import ExposureMapper
from .vaccine_mapper import to_vaccine_dto

__all__ = [
    "to_vaccine_dto",
    "ExposureMapper",
]
