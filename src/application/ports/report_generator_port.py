from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ReportGeneratorPort(Protocol):
    """
    Port for generating reports from application-level DTOs or primitives.
    Implementations must live in infrastructure/adapters and presentation/reporting layers,
    and they should not require domain entities.
    """

    def generate(self, data: object, destination: Path) -> Path:
        """Generate a report from the given data and write to destination.
        Returns the path to the generated artifact.
        The `data` type is intentionally broad to allow DTOs; avoid domain entities here.
        """
        ...
