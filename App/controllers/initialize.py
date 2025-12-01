from .user import create_user
from App.database import db
from App.models import Schedule, Shift
from datetime import datetime, timedelta

def initialize():
    db.drop_all()
    db.create_all()

    # Create users
    create_user('admin1', 'adminpass', 'admin')
    create_user('john_smith', 'password123', 'staff')
    create_user('jane_doe', 'password123', 'staff')
    create_user('alex_johnson', 'password123', 'staff')
    create_user('maria_garcia', 'password123', 'staff')
    create_user('robert_chen', 'password123', 'staff')
    create_user('emma_davis', 'password123', 'staff')

    # Create schedules
    schedule1 = Schedule(name="Week 1 Schedule", created_by=1)
    schedule2 = Schedule(name="Week 2 Schedule", created_by=1)
    db.session.add(schedule1)
    db.session.add(schedule2)
    db.session.commit()

    # Create shifts for this week
    today = datetime.now()
    base_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    
    shifts_data = [
        (2, base_date + timedelta(days=0, hours=9), base_date + timedelta(days=0, hours=17)),    # Monday
        (3, base_date + timedelta(days=0, hours=14), base_date + timedelta(days=0, hours=22)),   # Monday
        (4, base_date + timedelta(days=1, hours=9), base_date + timedelta(days=1, hours=17)),    # Tuesday
        (5, base_date + timedelta(days=1, hours=14), base_date + timedelta(days=1, hours=22)),   # Tuesday
        (6, base_date + timedelta(days=2, hours=9), base_date + timedelta(days=2, hours=17)),    # Wednesday
        (7, base_date + timedelta(days=2, hours=14), base_date + timedelta(days=2, hours=22)),   # Wednesday
        (2, base_date + timedelta(days=3, hours=9), base_date + timedelta(days=3, hours=17)),    # Thursday
        (3, base_date + timedelta(days=3, hours=14), base_date + timedelta(days=3, hours=22)),   # Thursday
        (4, base_date + timedelta(days=4, hours=9), base_date + timedelta(days=4, hours=17)),    # Friday
        (5, base_date + timedelta(days=4, hours=14), base_date + timedelta(days=4, hours=22)),   # Friday
    ]

    for staff_id, start, end in shifts_data:
        shift = Shift(
            schedule_id=schedule1.id,
            staff_id=staff_id,
            start_time=start,
            end_time=end
        )
        db.session.add(shift)
    
    db.session.commit()
