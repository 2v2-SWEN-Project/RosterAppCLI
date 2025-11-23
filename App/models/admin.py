from App.database import db
from .user import User


class Admin(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "admin")

    def get_json(self):
        base = super().get_json()
        # admin-specific info can be added here
        return base
