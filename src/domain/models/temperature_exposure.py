from dataclasses import dataclass


@dataclass(frozen=True)
class TemperatureExposure:
    """
    Represents a duration of exposure to a specific temperature.
    This is a pure domain concept, independent of timestamps or clock time.
    """

    temperature: float
    duration_minutes: float

    def __post_init__(self):
        if self.duration_minutes < 0:
            raise ValueError("Duration cannot be negative")
