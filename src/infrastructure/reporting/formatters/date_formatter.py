# src/infrastructure/reporting/formatters/date_formatter.py
from datetime import datetime
from typing import Dict

AR_WEEKDAYS: Dict[int, str] = {
    0: "الاثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

EN_WEEKDAYS: Dict[int, str] = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


class DateFormatter:
    @staticmethod
    def format_date(date_obj: datetime, locale: str = "en") -> str:
        """Format date per locale.

        - 'ar' -> yyyy/MM/dd
        - 'en' -> dd/MM/yyyy
        """
        if not isinstance(date_obj, datetime):
            raise TypeError("date_obj must be datetime")

        if locale == "ar":
            return date_obj.strftime("%Y/%m/%d")

        # default english
        return date_obj.strftime("%d/%m/%Y")

    @staticmethod
    def format_date_with_day(date_obj: datetime, locale: str = "en") -> str:
        """Format date with weekday name."""
        date_str = DateFormatter.format_date(date_obj, locale)
        weekday = date_obj.weekday()

        if locale == "ar":
            return f"{date_str} - {AR_WEEKDAYS.get(weekday, '')}"

        return f"{date_str} - {EN_WEEKDAYS.get(weekday, '')}"