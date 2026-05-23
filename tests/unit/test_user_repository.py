import pytest
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User, UserRole
from app.repositories.user_repository import (
    get_user_by_username,
    get_user_by_id,
    create_user,
)


def test_get_user_by_username_success(app):
    with app.app_context():
        user = User()
        user.username = "student01"
        user.password_hash = generate_password_hash("123456")
        user.role = UserRole.STUDENT
        user.is_active_account = True
        db.session.add(user)
        db.session.commit()

        found_user = get_user_by_username("student01")

        assert found_user is not None
        assert found_user.username == "student01"
        assert found_user.role == UserRole.STUDENT


def test_get_user_by_username_not_found(app):
    with app.app_context():
        found_user = get_user_by_username("nonexistent")

        assert found_user is None


def test_get_user_by_username_with_none(app):
    with app.app_context():
        found_user = get_user_by_username(None)

        assert found_user is None


def test_get_user_by_id_success(app):
    with app.app_context():
        user = User()
        user.username = "admin01"
        user.password_hash = generate_password_hash("123456")
        user.role = UserRole.ADMIN
        user.is_active_account = True
        db.session.add(user)
        db.session.commit()

        found_user = get_user_by_id(user.id)

        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.username == "admin01"
        assert found_user.role == UserRole.ADMIN


def test_get_user_by_id_not_found(app):
    with app.app_context():
        found_user = get_user_by_id(9999)

        assert found_user is None


def test_create_user_success(app):
    with app.app_context():
        password_hash = generate_password_hash("password123")

        created_user = create_user(
            username="newuser",
            password_hash=password_hash,
            role=UserRole.STUDENT,
        )

        assert created_user.id is not None
        assert created_user.username == "newuser"
        assert created_user.role == UserRole.STUDENT
        assert created_user.is_active_account is True

        found_user = get_user_by_id(created_user.id)
        assert found_user is not None
        assert found_user.username == "newuser"


def test_create_user_inactive(app):
    with app.app_context():
        password_hash = generate_password_hash("password123")

        created_user = create_user(
            username="inactiveuser",
            password_hash=password_hash,
            role=UserRole.STUDENT,
            is_active_account=False,
        )

        assert created_user.id is not None
        assert created_user.username == "inactiveuser"
        assert created_user.is_active_account is False

        found_user = get_user_by_id(created_user.id)
        assert found_user is not None
        assert found_user.is_active_account is False


def test_create_user_admin_role(app):
    with app.app_context():
        password_hash = generate_password_hash("password123")

        created_user = create_user(
            username="adminuser",
            password_hash=password_hash,
            role=UserRole.ADMIN,
            is_active_account=True,
        )

        assert created_user.role == UserRole.ADMIN

        found_user = get_user_by_username("adminuser")
        assert found_user.role == UserRole.ADMIN

