from datetime import date

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    Course,
    CourseClass,
    Enrollment,
    EnrollmentStatus,
    Room,
    Semester,
    Student,
    User,
    UserRole,
)


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


def test_admin_create_course_class_duplicate_code_route_fail(app, client):
    """Test case 3: Không cho tạo mã lớp trùng"""
    with app.app_context():
        admin_user = create_user("admin01", UserRole.ADMIN)
        course, semester, room = create_base_data()
        login_as(client, admin_user)

        # Create first class
        response1 = client.post(
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
        assert response1.status_code == 200
        assert "Tạo lớp học phần thành công".encode("utf-8") in response1.data

        # Try to create another class with the same code
        response2 = client.post(
            "/admin/classes/create",
            data={
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 3,
                "start_period": 4,
                "end_period": 6,
            },
        )

        assert response2.status_code == 400
        assert "đã tồn tại".encode("utf-8") in response2.data


def test_admin_create_course_class_same_room_different_time_route_success(app, client):
    """Test case 5: Cho tạo cùng phòng nhưng khác tiết"""
    with app.app_context():
        admin_user = create_user("admin01", UserRole.ADMIN)
        course, semester, room = create_base_data()
        login_as(client, admin_user)

        # Create first class
        response1 = client.post(
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
        assert response1.status_code == 200
        assert "Tạo lớp học phần thành công".encode("utf-8") in response1.data

        # Create second class in same room but different time
        response2 = client.post(
            "/admin/classes/create",
            data={
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-02",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 4,
                "end_period": 6,
            },
            follow_redirects=True,
        )

        assert response2.status_code == 200
        assert "Tạo lớp học phần thành công".encode("utf-8") in response2.data


def test_admin_create_course_class_same_time_different_room_route_success(app, client):
    """Test case 6: Cho tạo cùng tiết nhưng khác phòng"""
    with app.app_context():
        admin_user = create_user("admin01", UserRole.ADMIN)
        
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
        room_a = Room(code="A101", capacity=50)
        room_b = Room(code="B202", capacity=40)

        db.session.add_all([course, semester, room_a, room_b])
        db.session.commit()
        
        login_as(client, admin_user)

        # Create first class
        response1 = client.post(
            "/admin/classes/create",
            data={
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room_a.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            },
            follow_redirects=True,
        )
        assert response1.status_code == 200
        assert "Tạo lớp học phần thành công".encode("utf-8") in response1.data

        # Create second class in different room but same time
        response2 = client.post(
            "/admin/classes/create",
            data={
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-02",
                "max_students": 40,
                "status": "OPEN",
                "room_id": room_b.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            },
            follow_redirects=True,
        )

        assert response2.status_code == 200
        assert "Tạo lớp học phần thành công".encode("utf-8") in response2.data


def test_admin_delete_course_class_without_enrollment_route_success(app, client):
    """Test case 8: Cho xoá lớp chưa có sinh viên đăng ký"""
    with app.app_context():
        admin_user = create_user("admin01", UserRole.ADMIN)
        course, semester, room = create_base_data()
        login_as(client, admin_user)

        # Create a class
        response_create = client.post(
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
        assert response_create.status_code == 200

        # Get the created class
        course_class = CourseClass.query.filter_by(class_code="IT001-01").first()
        assert course_class is not None

        # Delete the class
        response_delete = client.post(
            f"/admin/classes/{course_class.id}/delete",
            follow_redirects=True,
        )

        assert response_delete.status_code == 200
        assert "Xoá lớp học phần thành công".encode("utf-8") in response_delete.data
        
        # Verify class is deleted
        deleted_class = CourseClass.query.filter_by(id=course_class.id).first()
        assert deleted_class is None


def test_admin_delete_course_class_with_enrollment_route_fail(app, client):
    """Test case 7: Không cho xoá lớp đã có sinh viên đăng ký"""
    with app.app_context():
        admin_user = create_user("admin01", UserRole.ADMIN)
        course, semester, room = create_base_data()
        login_as(client, admin_user)

        # Create a class
        response_create = client.post(
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
        assert response_create.status_code == 200

        course_class = CourseClass.query.filter_by(class_code="IT001-01").first()
        assert course_class is not None

        # Create a student and enroll
        student_user = create_user("student01", UserRole.STUDENT)
        student = Student(
            user_id=student_user.id,
            student_code="SV001",
            full_name="Nguyen Van A",
            major="CNTT",
        )
        db.session.add(student)
        db.session.commit()

        enrollment = Enrollment(
            student_id=student.id,
            course_class_id=course_class.id,
            semester_id=semester.id,
            status=EnrollmentStatus.REGISTERED,
        )
        db.session.add(enrollment)
        db.session.commit()

        # Try to delete the class with students
        response_delete = client.post(
            f"/admin/classes/{course_class.id}/delete",
            follow_redirects=True,
        )

        assert response_delete.status_code == 200
        assert "Không được xoá lớp".encode("utf-8") in response_delete.data
        
        # Verify class still exists
        existing_class = CourseClass.query.filter_by(id=course_class.id).first()
        assert existing_class is not None
