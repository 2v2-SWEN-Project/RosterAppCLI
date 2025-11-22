from App.models import User
from App.database import db

def login(username, password):
    result = db.session.execute(db.select(User).filter_by(username=username))
    user = result.scalar_one_or_none()
    if user and user.check_password(password):
        return user  # Return user object directly, no JWT
    return None

def loginCLI(username, password):
    result = db.session.execute(db.select(User).filter_by(username=username))
    user = result.scalar_one_or_none()
    if user and user.check_password(password):
        return {"message": "Login successful", "user_id": user.id}
    return {"message": "Invalid username or password"}

def logout(username):
    # No authentication/session to clear, just a stub
    result = db.session.execute(db.select(User).filter_by(username=username))
    user = result.scalar_one_or_none()
    if not user:
        return {"message": "User not found"}
    return {"message": f"User {username} logged out (no session)"}
