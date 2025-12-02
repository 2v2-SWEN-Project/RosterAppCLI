from datetime import datetime
from App.database import db


class ShiftSwapRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requesting_staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    requested_staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey("shift.id"), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending, approved, denied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requesting_staff = db.relationship("Staff", foreign_keys=[requesting_staff_id], backref="swap_requests_made")
    requested_staff = db.relationship("Staff", foreign_keys=[requested_staff_id], backref="swap_requests_received")
    shift = db.relationship("Shift", backref="swap_requests")

    def get_json(self):
        return {
            "id": self.id,
            "requesting_staff_id": self.requesting_staff_id,
            "requesting_staff_name": self.requesting_staff.username if self.requesting_staff else None,
            "requested_staff_id": self.requested_staff_id,
            "requested_staff_name": self.requested_staff.username if self.requested_staff else None,
            "shift_id": self.shift_id,
            "shift_date": self.shift.start_time.isoformat() if self.shift else None,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
