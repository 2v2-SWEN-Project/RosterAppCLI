from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Set
from collections import defaultdict


class ShiftSchedulingStrategy(ABC):
    """
    Interface for scheduling strategies.
    
    NOTE: Model layer only calculates/scores. Database queries are handled in the Controller layer.
    See: App/controllers/schedule_controller.py for usage.
    """

    @abstractmethod
    def score_staff(self, stats: Dict[int, Dict[str, any]]) -> int:
        """
        Score eligible staff to determine who should get the shift.
        
        Args:
            stats: Dictionary of staff stats (passed in by controller after querying DB)
        
        Returns:
            staff_id (int) with the best score (lowest value)
        """
        raise NotImplementedError()


class EvenDistributionStrategy(ShiftSchedulingStrategy):
    """Distribute the total number of shifts as evenly as possible across eligible staff.

    Tracks shiftsAssigned and hoursAssigned per staff. For each shift (in date/time order),
    determines eligible staff and chooses the one with the lowest shiftsAssigned
    (tie-break: lower hoursAssigned, then stable/random choice).

    Checks:
    - If feasible, the difference between max and min shiftsAssigned across staff is ≤ 1.
    - No hard-constraint violations.
    
    NOTE: This class is a pure calculator. The Controller queries the database and passes stats.
    """

    def __init__(self, eligible_staff_ids: Optional[List[int]] = None):
        """Initialize with optional list of eligible staff IDs."""
        self.eligible_staff_ids = eligible_staff_ids or []

    @staticmethod
    def calculate_shift_duration_hours(start_time: datetime, end_time: datetime) -> float:
        """Pure calculation: shift duration in hours."""
        delta = end_time - start_time
        return delta.total_seconds() / 3600.0

    def score_staff(self, stats: Dict[int, Dict[str, float]]) -> int:
        """
        Score staff based on shift and hour counts.
        
        Args:
            stats: {staff_id: {"shifts_assigned": int, "hours_assigned": float}, ...}
        
        Returns:
            Best staff_id (lowest shifts_assigned, then lowest hours_assigned)
        """
        if not stats:
            raise ValueError("No staff stats provided")

        return min(
            stats.keys(),
            key=lambda sid: (stats[sid]["shifts_assigned"], stats[sid]["hours_assigned"])
        )


class MinDaysPerWeekStrategy(ShiftSchedulingStrategy):
    """Minimize the number of distinct days worked per staff (cluster shifts into fewer days).

    Group shifts by day. When assigning a shift, prefer staff who already have a shift on that day.
    Penalize assigning a shift that would create a new work day for a staff member.

    Checks:
    - Average number of distinct days worked per staff is ≤ the Even strategy baseline.
    - No hard-constraint violations.
    
    NOTE: This class is a pure calculator. The Controller queries the database and passes stats.
    """

    def __init__(self, eligible_staff_ids: Optional[List[int]] = None):
        """Initialize with optional list of eligible staff IDs."""
        self.eligible_staff_ids = eligible_staff_ids or []

    def score_staff(self, stats: Dict[int, Set[str]], target_day: str) -> int:
        """
        Score staff based on whether they already work the target day.
        
        Args:
            stats: {staff_id: {"YYYY-MM-DD", "YYYY-MM-DD", ...}, ...}  (set of work dates)
            target_day: "YYYY-MM-DD" string
        
        Returns:
            Best staff_id (prefers already assigned to target_day)
        """
        if not stats:
            raise ValueError("No staff stats provided")

        def score(sid):
            days_set = stats.get(sid, set())
            if target_day in days_set:
                # Already works this day—prefer (score 0)
                return (0, len(days_set))
            else:
                # Would create new work day—penalize (score 1)
                return (1, len(days_set))

        return min(self.eligible_staff_ids, key=score)


class BalancedDayNightStrategy(ShiftSchedulingStrategy):
    """Keep the Day/Night shift balance fair for each staff member.

    Track dayCount and nightCount per staff. For a Day shift, prefer staff whose dayCount
    is currently low relative to nightCount, and vice versa for Night shifts.
    Include load (total hours/shifts) in the score to avoid overloading one person.

    Checks:
    - For each staff member, |dayCount − nightCount| is kept small or improved.
    - No hard-constraint violations.
    
    NOTE: This class is a pure calculator. The Controller queries the database and passes stats.
    """

    def __init__(self, eligible_staff_ids: Optional[List[int]] = None, day_shift_hours: Optional[tuple] = None):
        """
        Initialize the strategy.

        Args:
            eligible_staff_ids: List of staff IDs to consider.
            day_shift_hours: Tuple (start_hour, end_hour) defining day shifts (e.g., (6, 18)).
        """
        self.eligible_staff_ids = eligible_staff_ids or []
        self.day_shift_hours = day_shift_hours or (6, 18)

    @staticmethod
    def is_day_shift(start_time: datetime, day_shift_hours: tuple = (6, 18)) -> bool:
        """Pure calculation: determine if shift is day or night based on start hour."""
        hour = start_time.hour
        return day_shift_hours[0] <= hour < day_shift_hours[1]

    def score_staff(self, stats: Dict[int, Dict[str, any]], is_day: bool) -> int:
        """
        Score staff based on day/night balance.
        
        Args:
            stats: {staff_id: {"day_count": int, "night_count": int, "total_hours": float}, ...}
            is_day: True if assigning a day shift, False if night shift
        
        Returns:
            Best staff_id (most balanced day/night distribution)
        """
        if not stats:
            raise ValueError("No staff stats provided")

        def score(sid):
            s = stats.get(sid, {"day_count": 0, "night_count": 0, "total_hours": 0})
            day_count = s["day_count"]
            night_count = s["night_count"]
            total_hours = s["total_hours"]

            # Balance score: prefer low count of the shift type being assigned
            if is_day:
                balance_score = day_count - night_count
            else:
                balance_score = night_count - day_count

            # Load score: penalize high total hours
            load_score = total_hours

            return (balance_score, load_score)

        return min(self.eligible_staff_ids, key=score)
