from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User, UserRole


def create_test_user(
    username="student01",
    password="123456",
    role=UserRole.STUDENT,
    active=True
):
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        is_active_account=active
    )

    db.session.add(user)
    db.session.commit()

    return user


def login(client, username="student01", password="123456"):
    return client.post("/login", data={
        "username": username,
        "password": password
    })


def test_login_page_return_200(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "Đăng nhập".encode("utf-8") in response.data


def test_student_login_success_redirect_to_student_dashboard(app, client):
    with app.app_context():
        create_test_user()

    response = login(client, "student01", "123456")

    assert response.status_code == 302
    assert "/student/dashboard" in response.location


def test_admin_login_success_redirect_to_admin_dashboard(app, client):
    with app.app_context():
        create_test_user(username="admin01", role=UserRole.ADMIN)

    response = login(client, "admin01", "123456")

    assert response.status_code == 302
    assert "/admin/dashboard" in response.location


def test_login_wrong_password_return_401(app, client):
    with app.app_context():
        create_test_user()

    response = login(client, "student01", "wrongpass")

    assert response.status_code == 401
    assert b"Invalid username or password" in response.data


def test_inactive_account_login_return_401(app, client):
    with app.app_context():
        create_test_user(username="locked01", active=False)

    response = login(client, "locked01", "123456")

    assert response.status_code == 401
    assert b"Account is inactive" in response.data


def test_guest_cannot_access_student_dashboard(client):
    response = client.get("/student/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.location


def test_guest_cannot_access_admin_dashboard(client):
    response = client.get("/admin/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.location


def test_student_cannot_access_admin_dashboard(app, client):
    with app.app_context():
        create_test_user()

    login(client, "student01", "123456")

    response = client.get("/admin/dashboard")

    assert response.status_code == 403


def test_admin_cannot_access_student_dashboard(app, client):
    with app.app_context():
        create_test_user(username="admin01", role=UserRole.ADMIN)

    login(client, "admin01", "123456")

    response = client.get("/student/dashboard")

    assert response.status_code == 403


def test_logout_redirect_to_login(app, client):
    with app.app_context():
        create_test_user()

    login(client, "student01", "123456")

    response = client.get("/logout")

    assert response.status_code == 302
    assert "/login" in response.location


def test_logged_in_student_access_login_redirect_to_student_dashboard(app, client):
    """Test that a logged-in student accessing /login redirects to student dashboard"""
    with app.app_context():
        create_test_user()

    login(client, "student01", "123456")

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 302
    assert "/student/dashboard" in response.location


def test_logged_in_admin_access_login_redirect_to_admin_dashboard(app, client):
    """Test that a logged-in admin accessing /login redirects to admin dashboard"""
    with app.app_context():
        create_test_user(username="admin01", role=UserRole.ADMIN)

    login(client, "admin01", "123456")

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 302
    assert "/admin/dashboard" in response.location
