from App.models import Shift
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

def get_combined_roster(staff_id):
    staff = get_user(staff_id)
    if not staff or staff.role != "staff":
        raise PermissionError("Only staff can view roster")
    return [shift.get_json() for shift in Shift.query.order_by(Shift.start_time).all()]


def clock_in(staff_id, shift_id):
    shift = db.session.get(Shift, shift_id)
    if not shift:
        raise ValueError("Invalid shift for staff")
    if shift.staff_id != staff_id:
        raise PermissionError("Only the assigned staff can clock in to this shift.")
    if shift.clock_in:
        raise ValueError(f"Shift {shift_id} has already been clocked in at {shift.clock_in}.")
    shift.clock_in = datetime.now()
    db.session.commit()
    return shift


def clock_out(staff_id, shift_id):
    shift = db.session.get(Shift, shift_id)
    if not shift:
        raise ValueError("Invalid shift for staff")
    if shift.staff_id != staff_id:
        raise PermissionError("Only the assigned staff can clock out of this shift.")
    if shift.clock_out:
        raise ValueError(f"Shift {shift_id} has already been clocked out at {shift.clock_out}.")
    shift.clock_out = datetime.now()
    db.session.commit()
    return shift

def get_shift(shift_id):
    shift = db.session.get(Shift, shift_id)
    return shift