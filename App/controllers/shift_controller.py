from datetime import datetime
from typing import Dict, Any, Tuple

from App.database import db
from App.models import Staff, Shift


class ShiftController:

    @staticmethod
    def clock_in(staff_id: int, shift_id: int) -> Tuple[Dict[str, Any], int]:
        shift = Shift.query.get(shift_id)
        
        if not shift:
            return {"error": "Shift not found"}, 404
        
        if shift.staff_id != staff_id:
            return {"error": "Invalid staff for shift."}, 404
        
        if shift.clock_in is not None:
            return {"error": "Already clocked in"}, 400
        
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
        
        if shift.clock_in is None:
            return {"error": "Not clocked in"}, 400
        
        if shift.clock_out is not None:
            return {"error": "Already clocked out"}, 400
        
        shift.clock_out = datetime.utcnow()
        db.session.commit()

        return shift.get_json(), 200

    @staticmethod
    def get_staff_shifts(staff_id: int) -> Tuple[Dict[str, Any], int]:
        staff = Staff.query.get(staff_id)
        if not staff:
            return {"error": "Staff not found"}, 404
        
        shifts = Shift.query.filter_by(staff_id=staff_id).order_by(Shift.start_time.desc()).all()
        shifts_json = [shift.get_json() for shift in shifts]

        return {"shifts": shifts_json, "count": len(shifts_json)}, 200

    @staticmethod
    def update_shift(
        shift_id: int,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> Tuple[Dict[str, Any], int]:
        shift = Shift.query.get(shift_id)
        if not shift:
            return {"error": "Shift not found"}, 404
        
        if shift.clock_in or shift.clock_out:
            return {"error": "Cannot update shift after clock in/out"}, 400
        
        if start_time and end_time and start_time >= end_time:
            return {"error": "Start time must be before end time"}, 400
        
        if start_time:
            shift.start_time = start_time
        if end_time:
            shift.end_time = end_time
        
        db.session.add(shift)
        db.session.commit()

        return shift.get_json(), 200

    @staticmethod
    def delete_shift(shift_id: int) -> Tuple[Dict[str, Any], int]:
        shift = Shift.query.get(shift_id)
        if not shift:
            return {"error": "Shift not found"}, 404
        
        if shift.clock_in or shift.clock_out:
            return {"error": "Cannot delete shift after clock in/out"}, 400
        
        db.session.delete(shift)
        db.session.commit()

        return {"id": shift_id, "deleted": True}, 200

    @staticmethod
    def get_shift_report(
        start_date: datetime,
        end_date: datetime,
        staff_id: int = None
    ) -> Tuple[Dict[str, Any], int]:
        query = Shift.query.filter(Shift.start_time >= start_date, Shift.end_time <= end_date)
        
        if staff_id:
            query = query.filter_by(staff_id=staff_id)

        shifts = query.all()
        
        total_shifts = len(shifts)
        total_hours = sum([shift.calculate_shift_duration_hours() for shift in shifts])
        avg_hours = total_hours / total_shifts if total_shifts > 0 else 0
        
        report = {
            "total_shifts": total_shifts,
            "total_hours": total_hours,
            "average_hours_per_shift": avg_hours
        }

        return report, 200
