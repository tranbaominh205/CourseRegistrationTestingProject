from app.models import User
from app.extensions import db


def get_user_by_username(username):
    if username is None:
        return None

    return User.query.filter_by(username=username).first()


def get_user_by_id(user_id):
    return db.session.get(User, user_id)


def create_user(username, password_hash, role, is_active_account=True):
    user = User()
    user.username = username
    user.password_hash = password_hash
    user.role = role
    user.is_active_account = is_active_account

    db.session.add(user)
    db.session.commit()

    return user