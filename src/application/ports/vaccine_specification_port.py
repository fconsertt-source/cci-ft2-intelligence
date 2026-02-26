from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.value_objects.vaccine_specification import VaccineSpecification


class VaccineSpecificationPort(ABC):
    """
    Port for accessing vaccine-specific thermal specifications.
    Follows same pattern as Ft2ReaderPort in Phase 5.
    """

    @abstractmethod
    def get_spec(self, vaccine_type: str) -> Optional[VaccineSpecification]:
        """
        Get thermal specification for a vaccine type.
        """
        raise NotImplementedError
