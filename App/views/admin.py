from flask_admin.contrib.sqla import ModelView
# Removed flask_jwt_extended import
from flask_admin import Admin
from flask import flash, redirect, url_for, request
from App.database import db
from App.models import User

class AdminView(ModelView):
    def is_accessible(self):
        # No authentication, always accessible
        return True

    def inaccessible_callback(self, name, **kwargs):
        # No authentication, so this should not be called
        flash("Login to access admin")
        return redirect(url_for('index_page', next=request.url))

def setup_admin(app):
    admin = Admin(app, name='FlaskMVC', template_mode='bootstrap3')
    admin.add_view(AdminView(User, db.session))