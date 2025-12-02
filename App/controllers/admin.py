from App.models import Shift, Schedule, Staff, ShiftSwapRequest
from App.database import db
from datetime import datetime, timedelta
from App.controllers.user import get_user
from sqlalchemy import func

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

def get_total_staff_count():
    """Count total number of staff members."""
    return db.session.query(func.count(Staff.id)).scalar() or 0

def get_shifts_this_week():
    """Count shifts scheduled for this week."""
    today = datetime.utcnow()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return db.session.query(func.count(Shift.id)).filter(
        Shift.start_time >= week_start,
        Shift.start_time <= week_end
    ).scalar() or 0

def get_pending_swap_requests():
    """Get all pending shift swap requests."""
    requests = ShiftSwapRequest.query.filter_by(status="pending").all()
    return [req.get_json() for req in requests]

def get_staff_attendance():
    """Get attendance data for all staff (with clock in/out times and hours)."""
    staff_members = Staff.query.all()
    attendance_data = []
    
    for staff in staff_members:
        shifts = Shift.query.filter_by(staff_id=staff.id).all()
        
        for shift in shifts:
            hours = 0
            status = "Absent"
            
            if shift.clock_in and shift.clock_out:
                delta = shift.clock_out - shift.clock_in
                hours = round(delta.total_seconds() / 3600, 1)
                status = "Present"
            elif shift.clock_in and not shift.clock_out:
                status = "Clocked In"
            
            attendance_data.append({
                "staff_name": staff.username,
                "staff_id": staff.id,
                "clock_in": shift.clock_in.strftime("%I:%M %p") if shift.clock_in else "—",
                "clock_out": shift.clock_out.strftime("%I:%M %p") if shift.clock_out else "—",
                "hours": hours,
                "status": status,
                "shift_id": shift.id
            })
    
    return attendance_data

def approve_swap_request(request_id):
    """Approve a shift swap request."""
    swap_req = db.session.get(ShiftSwapRequest, request_id)
    if not swap_req:
        raise ValueError("Swap request not found")
    swap_req.status = "approved"
    db.session.commit()
    return swap_req

def deny_swap_request(request_id):
    """Deny a shift swap request."""
    swap_req = db.session.get(ShiftSwapRequest, request_id)
    if not swap_req:
        raise ValueError("Swap request not found")
    swap_req.status = "denied"
    db.session.commit()
    return swap_req