class HERCalculator:
    """
    حساب Heat Exposure Ratio (HER)
    """

    def calculate(self, exposure_minutes: int, full_duration: int) -> float:
        if full_duration <= 0:
            return 0.0
        return min(exposure_minutes / full_duration, 1.0)
