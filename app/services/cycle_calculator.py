from datetime import date, timedelta
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
    def calculate_ovulation_days(cycle_start: date, cycle_length: int = 28) -> List[date]:
        """
        Calculate ovulation days (3-day window around ovulation).
        Ovulation typically occurs 14 days before the next period.
        """
        ovulation_day = cycle_start + timedelta(days=cycle_length - 14)
        return [
            ovulation_day - timedelta(days=1),
            ovulation_day,
            ovulation_day + timedelta(days=1),
        ]

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
            cycles: List of cycle dictionaries with start_date, end_date, cycle_length, period_length
            prioritize_actual: If True, actual (ended) cycles take priority over predictions
        """
        for cycle in cycles:
            cycle_start = cycle.get("start_date")
            cycle_end = cycle.get("end_date")
            period_length = cycle.get("period_length", 5)
            cycle_length = cycle.get("cycle_length", 28)

            if not cycle_start:
                continue

            # Check period days (only for actual cycles with end_date)
            if cycle_end:
                period_days = CycleCalculator.calculate_period_days(
                    cycle_start, period_length
                )
                if target_date in period_days:
                    return "period"

            # Check ovulation days
            if cycle_length:
                ovulation_days = CycleCalculator.calculate_ovulation_days(
                    cycle_start, cycle_length
                )
                if target_date in ovulation_days:
                    return "ovulation"

                # Check fertile days
                fertile_days = CycleCalculator.calculate_fertile_days(
                    cycle_start, cycle_length
                )
                if target_date in fertile_days:
                    return "fertile"

        return None

    @staticmethod
    def predict_next_cycles(
        cycles: List[Dict],
        num_predictions: int = 3
    ) -> List[Dict]:
        """
        Predict the next N cycles based on historical data.
        This is a simple average-based prediction that can be replaced with AI.

        Returns list of predicted cycles with start_date, predicted_end, cycle_length
        """
        if not cycles:
            return []

        # Calculate average cycle length from historical data
        cycle_lengths = [
            c.get("cycle_length") for c in cycles if c.get("cycle_length")
        ]
        avg_cycle_length = (
            sum(cycle_lengths) // len(cycle_lengths) if cycle_lengths else 28
        )

        # Calculate average period length
        period_lengths = [
            c.get("period_length") for c in cycles if c.get("period_length")
        ]
        avg_period_length = (
            sum(period_lengths) // len(period_lengths) if period_lengths else 5
        )

        # Start predictions from the last cycle
        last_cycle = cycles[0]  # Assuming sorted by date descending
        last_start = last_cycle.get("start_date")

        if not last_start:
            return []

        predictions = []
        current_start = last_start + timedelta(days=avg_cycle_length)

        for _ in range(num_predictions):
            predicted_end = current_start + timedelta(days=avg_period_length - 1)
            predictions.append({
                "start_date": current_start,
                "predicted_end": predicted_end,
                "cycle_length": avg_cycle_length,
                "period_length": avg_period_length,
                "is_predicted": True,
            })
            current_start += timedelta(days=avg_cycle_length)

        return predictions
