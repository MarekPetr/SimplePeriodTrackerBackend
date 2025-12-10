from datetime import date, datetime, timedelta
from typing import List, Dict, Optional


class CycleCalculator:
    """
    Handles all cycle-related calculations including period days, ovulation, and fertile windows.
    This can be replaced with AI-based predictions in the future.
    """

    @staticmethod
    def calculate_period_days(cycle_start: date, period_length: int = 5) -> List[date]:
        """Calculate which days are period days for a given cycle."""
        return [cycle_start + timedelta(days=i) for i in range(period_length)]

    @staticmethod
    def calculate_ovulation_day(cycle_start: date, cycle_length: int = 28) -> List[date]:
        return cycle_start + timedelta(days=cycle_length - 14)

    @staticmethod
    def calculate_fertile_days(cycle_start: date, cycle_length: int = 28) -> List[date]:
        """
        Calculate fertile window (5 days before ovulation to 1 day after).
        This gives the best chance for conception.
        """
        ovulation_day = cycle_start + timedelta(days=cycle_length - 14)
        fertile_start = ovulation_day - timedelta(days=5)
        fertile_end = ovulation_day + timedelta(days=1)

        fertile_days = []
        current = fertile_start
        while current <= fertile_end:
            fertile_days.append(current)
            current += timedelta(days=1)

        return fertile_days

    @staticmethod
    def get_day_type(
        target_date: date,
        cycles: List[Dict],
        prioritize_actual: bool = True
    ) -> Optional[str]:
        """
        Determine the type of a specific day based on cycle data.
        Returns: 'period', 'ovulation', 'fertile', or None

        Args:
            target_date: The date to check
            cycles: List of cycle dictionaries with period_start_date, period_end_date, cycle_length, period_length
            prioritize_actual: If True, actual (ended) cycles take priority over predictions
        """
        for cycle in cycles:
            cycle_start: datetime = cycle.get("period_start_date")
            cycle_end: datetime = cycle.get("period_end_date")
            period_length: int = cycle.get("period_length") or 5
            cycle_length: int = cycle.get("cycle_length")  # Don't default to 28

            if not cycle_start:
                continue

            # Check period days (only for actual cycles with period_end_date)
            if cycle_end:
                period_days = CycleCalculator.calculate_period_days(
                    cycle_start.date(), period_length
                )
                if target_date in period_days:
                    return "period"

            # Check ovulation and fertile days only if cycle_length is explicitly set
            if cycle_length:
                ovulation_day = CycleCalculator.calculate_ovulation_day(
                    cycle_start.date(), cycle_length
                )
                if target_date == ovulation_day:
                    return "ovulation"

                # Check fertile days
                fertile_days = CycleCalculator.calculate_fertile_days(
                    cycle_start.date(), cycle_length
                )
                if target_date in fertile_days:
                    return "fertile"

        return None

    @staticmethod
    def predict_next_cycle(
        cycles: List[Dict],
    ) -> Dict:
        """
        Predict cycles that fall within the target month based on historical data.
        Uses average of last 3 cycle lengths for prediction.

        Args:
            cycles: List of actual cycle dictionaries (sorted by date ascending)

        Returns list of predicted cycles with period_start_date, period_end_date, period_length, is_predicted
        """
        if not cycles:
            return {}

        # Calculate cycle lengths between consecutive cycles
        cycle_lengths = []
        for i in range(1, len(cycles)):
            prev_start = cycles[i-1].get("period_start_date")
            curr_start = cycles[i].get("period_start_date")
            if prev_start and curr_start:
                cycle_length = (curr_start - prev_start).days
                if cycle_length > 0:
                    cycle_lengths.append(cycle_length)

        # Calculate average of last 3 cycle lengths
        avg_cycle_length = 28  # Default
        if cycle_lengths:
            last_3_lengths = cycle_lengths[-3:] if len(cycle_lengths) >= 3 else cycle_lengths
            avg_cycle_length = sum(last_3_lengths) // len(last_3_lengths)

        # Calculate average period length
        period_lengths = [c.get("period_length") for c in cycles if c.get("period_length")]
        avg_period_length = sum(period_lengths) // len(period_lengths) if period_lengths else 5

        # Start predictions from the last actual cycle
        last_cycle = cycles[-1]  # Last cycle (sorted ascending)
        last_start: datetime = last_cycle.get("period_start_date")

        if not last_start:
            return {}

        next_start = last_start + timedelta(days=avg_cycle_length)
        predicted_end = next_start + timedelta(days=avg_period_length - 1)
        return {
            "period_start_date": next_start,
            "period_end_date": predicted_end,
            "period_length": avg_period_length,
            "is_predicted": True
        }
