import pytest
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User, UserRole
from app.services.auth_service import authenticate_user


def create_test_user(
    username="student01",
    password="123456",
    role=UserRole.STUDENT,
    active=True
):
    user = User()
    user.username = username
    user.password_hash = generate_password_hash(password)
    user.role = role
    user.is_active_account = active

    db.session.add(user)
    db.session.commit()

    return user


@pytest.mark.parametrize(
    "username, password, role",
    [
        ("student01", "123456", UserRole.STUDENT),  # LOGIN_TC01
        ("admin01", "123456", UserRole.ADMIN),      # LOGIN_TC02
    ]
)
def test_authenticate_user_success(app, username, password, role):
    with app.app_context():
        create_test_user(
            username=username,
            password=password,
            role=role,
            active=True
        )

        user, error = authenticate_user(username, password)

        assert user is not None
        assert error is None
        assert user.username == username
        assert user.role == role


@pytest.mark.parametrize(
    "test_id, username, password, expected_error",
    [
        (
            "LOGIN_TC03",
            "student01",
            "wrongpass",
            "Sai mật khẩu"
        ),
        (
            "LOGIN_TC04",
            "unknown",
            "123456",
            "Tài khoản không tồn tại"
        ),
        (
            "LOGIN_TC05",
            "",
            "123456",
            "Username and password are required"
        ),
        (
            "LOGIN_TC06",
            "student01",
            "",
            "Username and password are required"
        ),
        (
            "LOGIN_TC07",
            "",
            "",
            "Username and password are required"
        ),
    ]
)
def test_authenticate_user_failed_cases(
    app,
    test_id,
    username,
    password,
    expected_error
):
    with app.app_context():
        if test_id in ["LOGIN_TC03", "LOGIN_TC06"]:
            create_test_user(
                username="student01",
                password="123456",
                role=UserRole.STUDENT,
                active=True
            )

        user, error = authenticate_user(username, password)

        assert user is None
        assert error == expected_error


def test_authenticate_user_inactive_account(app):
    # LOGIN_TC08
    with app.app_context():
        create_test_user(
            username="locked01",
            password="123456",
            role=UserRole.STUDENT,
            active=False
        )

        user, error = authenticate_user("locked01", "123456")

        assert user is None
        assert error == "Account is inactive"


@pytest.mark.parametrize(
    "url",
    [
        "/student/dashboard",  # LOGIN_TC10
        "/admin/classes",      # LOGIN_TC11
    ]
)
def test_dashboard_requires_login(client, url):
    response = client.get(url, follow_redirects=False)

    assert response.status_code in [302, 401, 403]

    if response.status_code == 302:
        assert "/login" in response.location


def test_login_form_display(client):
    # LOGIN_TC12
    response = client.get("/login")

    assert response.status_code == 200

    html = response.data.decode("utf-8").lower()

    assert "username" in html
    assert "password" in html
    assert "login" in html