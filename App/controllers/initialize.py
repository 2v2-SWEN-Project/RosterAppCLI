from .user import create_user
from App.database import db
from App.models import Schedule, Shift
from datetime import datetime

def initialize():
    db.drop_all()
    db.create_all()

    create_user('bob', 'bobpass', 'admin')
    create_user('jane', 'janepass', 'staff')
    create_user('alice', 'alicepass', 'staff')
    create_user('tim', 'timpass', 'user')

    schedule = Schedule(
        name="Morning Shift",
        created_by=1
    )
    db.session.add(schedule)
    db.session.commit()

    shift1 = Shift(
        schedule_id=schedule.id,
        staff_id=2,
        start_time=datetime(2024, 10, 1, 8, 0, 0),  # Correctly passing datetime objects
        end_time=datetime(2024, 10, 1, 12, 0, 0)    # Correctly passing datetime objects
    )
    db.session.add(shift1)
    db.session.commit()
