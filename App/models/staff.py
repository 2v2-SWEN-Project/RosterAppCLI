from App.database import db
from .user import User


class Staff(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "staff",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "staff")

    def get_json(self, include_shifts: bool = False):
        base = super().get_json()
        # include basic shift summary for this staff member only when requested
        if include_shifts:
            base.update({
                "shifts": [s.get_json() for s in getattr(self, "shifts", [])]
            })
        return base


    def view_roster(self):
        """Return this staff member's shifts (as JSON list)."""
        return [s.get_json() for s in getattr(self, 'shifts', [])]
