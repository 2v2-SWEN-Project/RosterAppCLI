from App.models import Shift
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

from App.models import Shift, Schedule
from App.database import db
from datetime import datetime
from App.controllers.user import get_user

def create_schedule(admin_id, scheduleName):
    new_schedule = Schedule(
        created_by=admin_id,
        name=scheduleName,
        created_at=datetime.utcnow()
    )
    db.session.add(new_schedule)
    db.session.commit()
    return new_schedule

def schedule_shift(admin_id, staff_id, schedule_id, start_time, end_time):
    staff = get_user(staff_id)
    schedule = db.session.get(Schedule, schedule_id)
    if not staff or staff.role != "staff":
        raise PermissionError("Only staff can be assigned to a shift.")
    if not schedule:
        raise ValueError("Invalid schedule ID")
    new_shift = Shift(
        staff_id=staff_id,
        schedule_id=schedule_id,
        start_time=start_time,
        end_time=end_time
    )
    db.session.add(new_shift)
    db.session.commit()
    return new_shift

def get_shift_report(admin_id):
    admin = get_user(admin_id)
    if not admin or admin.role != "admin":
        raise PermissionError("Only admin can view shift report")
    return [shift.get_json() for shift in Shift.query.order_by(Shift.start_time).all()]