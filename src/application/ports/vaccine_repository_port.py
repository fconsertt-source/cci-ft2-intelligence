# src/application/ports/vaccine_repository_port.py
from typing import Protocol, Optional
from src.domain.entities.vaccine_batch import VaccineBatch

class VaccineRepositoryPort(Protocol):
    """Abstraction for vaccine batch persistence — Application layer depends ONLY on this."""
    
    def save_batch(self, batch: VaccineBatch) -> None:
        """Save or update a vaccine batch with its cumulative exposure."""
        ...
    
    def get_batch(self, batch_id: str) -> Optional[VaccineBatch]:
        """Retrieve a vaccine batch by ID."""
        ...
    
    def get_batch_history(self, batch_id: str) -> list[VaccineBatch]:
        """Retrieve full exposure history for a batch across cold chain stages."""
        ...