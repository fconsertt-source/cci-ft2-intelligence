from __future__ import annotations

from typing import Iterable, List

from src.application.ports.i_repository import IDataRepository
from src.application.dtos.center_dto import CenterDTO
from src.application.dtos.vaccine_dto import VaccineDTO
from src.infrastructure.utils.vaccine_library_loader import VaccineLibraryLoader


class Ft2RepositoryAdapter(IDataRepository):
    """
    Minimal concrete adapter implementing IDataRepository.
    This demo adapter sources vaccines from the VaccineLibraryLoader and returns
    a small synthetic set of Centers. It is sufficient to prove the Port wiring.
    """

    def load_centers(self) -> Iterable[CenterDTO]:
        # Minimal synthetic center list for wiring proof
        return [
            CenterDTO(center_id="C-001", name="Demo Center", location="N/A"),
        ]

    def load_vaccines(self) -> Iterable[VaccineDTO]:
        # Map a subset of library data into VaccineDTOs where possible
        lib = VaccineLibraryLoader.get_instance()
        vaccines: List[VaccineDTO] = []
        for vaccine_id, data in lib.vaccine_library.items():
            vaccines.append(
                VaccineDTO(
                    id=vaccine_id,
                    name=data.get("name", vaccine_id),
                    category=data.get("category", "general"),
                    full_loss_threshold_low=data.get("temp_requirements", {}).get("min_safe", 0.0),
                    full_loss_threshold_high=data.get("temp_requirements", {}).get("max_safe", 8.0),
                    shelf_life_days=int(data.get("shelf_life_days", 30)),
                    # Optional scientific fields left to defaults if DTO supports them
                )
            )
        return vaccines
