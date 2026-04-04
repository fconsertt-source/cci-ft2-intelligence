# src/infrastructure/reporting/formatters/number_formatter.py
from typing import Union


class NumberFormatter:
    @staticmethod
    def format_number(value: Union[int, float], locale: str = "en") -> str:
        """Always return western digits with dot as decimal separator."""
        if not isinstance(value, (int, float)):
            raise TypeError("value must be int or float")

        formatted = f"{value:.2f}" if isinstance(value, float) else str(value)

        # if locale-specific enhancements needed later, keep same digits.
        return formatted

    @staticmethod
    def format_temperature(value: Union[int, float], locale: str = "en") -> str:
        if not isinstance(value, (int, float)):
            raise TypeError("value must be numeric")

        base = NumberFormatter.format_number(value, locale)
        if locale == "ar":
            return f"{base}°م"
        return f"{base}°C"

    @staticmethod
    def format_percentage(value: Union[int, float], locale: str = "en") -> str:
        if not isinstance(value, (int, float)):
            raise TypeError("value must be numeric")

        base = NumberFormatter.format_number(value, locale)
        return f"{base}%"