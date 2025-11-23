from datetime import datetime
from App.database import db


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # who created the schedule (user id)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # optional links to the staff the schedule is for and the admin who owns it
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    shifts = db.relationship("Shift", backref="schedule", lazy=True)

    def shift_count(self):
        return len(self.shifts)

    def get_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "staff_id": self.staff_id,
            "admin_id": self.admin_id,
            "shift_count": self.shift_count(),
            "shifts": [shift.get_json() for shift in self.shifts]
        }


