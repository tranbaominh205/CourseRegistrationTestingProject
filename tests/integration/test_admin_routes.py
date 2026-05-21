from datetime import date

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Course, Room, Semester, User, UserRole


def create_user(username, role):
    user = User()
    user.username = username
    user.password_hash = generate_password_hash("123456")
    user.role = role
    user.is_active_account = True
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True


def create_base_data():
    course = Course(code="IT001", name="Nhập môn lập trình", credits=3)
    semester = Semester(
        name="Học kỳ 1",
        academic_year="2025-2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 30),
        registration_start_date=date(2025, 12, 1),
        registration_end_date=date(2026, 1, 15),
        is_active=True,
    )
    room = Room(code="A101", capacity=50)

    db.session.add_all([course, semester, room])
    db.session.commit()

    return course, semester, room


def test_student_cannot_access_admin_classes(app, client):
    with app.app_context():
        student_user = create_user("student01", UserRole.STUDENT)
        login_as(client, student_user)

        response = client.get("/admin/classes")

        assert response.status_code == 403


def test_admin_can_access_admin_classes(app, client):
    with app.app_context():
        admin_user = create_user("admin01", UserRole.ADMIN)
        login_as(client, admin_user)

        response = client.get("/admin/classes")

        assert response.status_code == 200
        assert "Academic Interface System".encode("utf-8") in response.data
        assert "Quản lý lớp học phần".encode("utf-8") in response.data


def test_admin_create_course_class_route_success(app, client):
    with app.app_context():
        admin_user = create_user("admin01", UserRole.ADMIN)
        course, semester, room = create_base_data()
        login_as(client, admin_user)

        response = client.post(
            "/admin/classes/create",
            data={
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert "Tạo lớp học phần thành công".encode("utf-8") in response.data


def test_admin_create_course_class_over_50_route_fail(app, client):
    with app.app_context():
        admin_user = create_user("admin01", UserRole.ADMIN)
        course, semester, room = create_base_data()
        login_as(client, admin_user)

        response = client.post(
            "/admin/classes/create",
            data={
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 51,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            },
        )

        assert response.status_code == 400
        assert "không được vượt quá 50".encode("utf-8") in response.data