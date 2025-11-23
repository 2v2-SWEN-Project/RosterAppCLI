from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any

from App.database import db
from App.models import (
    Admin,
    Staff,
    Shift,
    Schedule,
    EvenDistributionStrategy,
    MinDaysPerWeekStrategy,
    BalancedDayNightStrategy,
)


class ScheduleController:

    @staticmethod
    def clock_in(staff_id: int, shift_id: int) -> Tuple[Dict[str, Any], int]:
        shift = Shift.query.get(shift_id)
        
        if not shift:
            return {"error": "Shift not found"}, 404
        
        if shift.staff_id != staff_id:
            return {"error": "Invalid staff for shift."}, 404
        
        shift.clock_in = datetime.utcnow()
        db.session.commit()

        return shift.get_json(), 200

    @staticmethod
    def clock_out(staff_id: int, shift_id: int) -> Tuple[Dict[str, Any], int]:
        shift = Shift.query.get(shift_id)

        if not shift:
            return {"error": "Shift not found"}, 404
        
        if shift.staff_id != staff_id:
            return {"error": "Invalid staff for shift."}, 404
        
        shift.clock_out = datetime.utcnow()
        db.session.commit()

        return shift.get_json(), 200

    @staticmethod
    def _get_staff_stats(staff_ids: List[int]) -> Dict[int, Dict[str, float]]:
        stats = {}
        for staff_id in staff_ids:
            staff = Staff.query.get(staff_id)
            if staff:
                shifts = Shift.query.filter_by(staff_id=staff_id).all()
                shifts_assigned = len(shifts)
                hours_assigned = sum([shift.calculate_shift_duration_hours() for shift in shifts])
                stats[staff_id] = {"shifts_assigned": shifts_assigned, "hours_assigned": hours_assigned}
        return stats

    @staticmethod
    def _get_days_worked(staff_ids: List[int]) -> Dict[int, set]:
        days_worked = {}
        for staff_id in staff_ids:
            staff = Staff.query.get(staff_id)
            if staff:
                shifts = Shift.query.filter_by(staff_id=staff_id).all()
                worked_days = {shift.start_time.strftime("%Y-%m-%d") for shift in shifts}
                days_worked[staff_id] = worked_days
        return days_worked

    @staticmethod
    def _get_day_night_stats(staff_ids: List[int], day_shift_hours: Tuple[int, int] = (6, 18)) -> Dict[int, Dict[str, Any]]:
        stats = {}
        for staff_id in staff_ids:
            staff = Staff.query.get(staff_id)
            if staff:
                shifts = Shift.query.filter_by(staff_id=staff_id).all()
                day_count = 0
                night_count = 0
                total_hours = 0
                for shift in shifts:
                    is_day_shift = BalancedDayNightStrategy.is_day_shift(shift.start_time, day_shift_hours)
                    if is_day_shift:
                        day_count += 1
                    else:
                        night_count += 1
                    total_hours += shift.calculate_shift_duration_hours()

                stats[staff_id] = {
                    "day_count": day_count,
                    "night_count": night_count,
                    "total_hours": total_hours
                }
        return stats

    @staticmethod
    def auto_populate_schedule(
        schedule_id: int,
        strategy_type: str,  
        eligible_staff_ids: List[int],
        num_days: int = 7,
        shift_start_hour: int = 9,
        shift_end_hour: int = 17,
        day_shift_hours: Tuple[int, int] = (6, 18)
    ) -> Tuple[Dict[str, Any], int]:
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return {"error": "Schedule not found"}, 404
        if not eligible_staff_ids:
            return {"error": "No eligible staff IDs provided"}, 400
        if strategy_type not in ('even', 'min_days', 'balanced'):
            return {"error": "Invalid strategy type"}, 400
        
        if strategy_type == 'even':
            strategy = EvenDistributionStrategy()
        elif strategy_type == 'min_days':
            strategy = MinDaysPerWeekStrategy()
        else:
            strategy = BalancedDayNightStrategy()

        result_shifts = []
        current_datetime = datetime.utcnow()
        for day_offset in range(num_days):
            start_time = current_datetime + timedelta(days=day_offset, hours=shift_start_hour)
            end_time = current_datetime + timedelta(days=day_offset, hours=shift_end_hour)

            if strategy_type == 'even':
                stats = ScheduleController._get_staff_stats(eligible_staff_ids)
            elif strategy_type == 'min_days':
                stats = ScheduleController._get_days_worked(eligible_staff_ids)
            else:
                stats = ScheduleController._get_day_night_stats(eligible_staff_ids, day_shift_hours)

            best_staff_id = strategy.score_staff(stats)
            shift = Shift(staff_id=best_staff_id, start_time=start_time, end_time=end_time, schedule_id=schedule_id)
            db.session.add(shift)
            db.session.commit()
            result_shifts.append(shift.get_json())

        return {"shifts": result_shifts, "count": len(result_shifts)}, 201

    @staticmethod
    def schedule_shift_for_staff(
        admin_id: int,
        staff_id: int,
        start_time: datetime,
        end_time: datetime,
        schedule_id: int = None
    ) -> Tuple[Dict[str, Any], int]:
        admin = Admin.query.get(admin_id)
        if not admin:
            return {"error": "Admin not found or unauthorized"}, 404
        staff = Staff.query.get(staff_id)
        if not staff:
            return {"error": "Staff not found"}, 404
        if start_time >= end_time:
            return {"error": "Invalid time range"}, 400
        if schedule_id:
            schedule = Schedule.query.get(schedule_id)
            if not schedule:
                return {"error": "Schedule not found"}, 404
        
        shift = Shift(staff_id=staff_id, start_time=start_time, end_time=end_time, schedule_id=schedule_id)
        db.session.add(shift)
        db.session.commit()

        return shift.get_json(), 201

    @staticmethod
    def view_shift(shift_id: int) -> Tuple[Dict[str, Any], int]:
        shift = Shift.query.get(shift_id)
        if not shift:
            return {"error": "Shift not found"}, 404
        return shift.get_json(), 200

    @staticmethod
    def get_schedule_shifts(schedule_id: int) -> Tuple[Dict[str, Any], int]:
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return {"error": "Schedule not found"}, 404
        shifts = Shift.query.filter_by(schedule_id=schedule_id).all()
        shifts_json = [shift.get_json() for shift in shifts]
        return {"shifts": shifts_json}, 200
