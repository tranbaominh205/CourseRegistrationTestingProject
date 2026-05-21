from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    ClassSchedule,
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
from app.services.admin_service import (
    AdminServiceError,
    create_course_class,
    delete_course_class,
)


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


def test_admin_create_course_class_success(app):
    with app.app_context():
        course, semester, room = create_base_data()

        course_class = create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-01",
            "max_students": 50,
            "status": "OPEN",
            "room_id": room.id,
            "day_of_week": 2,
            "start_period": 1,
            "end_period": 3,
        })

        assert course_class.id is not None
        assert course_class.class_code == "IT001-01"
        assert course_class.max_students == 50
        assert len(course_class.schedules) == 1


def test_admin_create_course_class_max_students_over_50_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="không được vượt quá 50"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 51,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_room_conflict_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-01",
            "max_students": 50,
            "status": "OPEN",
            "room_id": room.id,
            "day_of_week": 2,
            "start_period": 1,
            "end_period": 3,
        })

        with pytest.raises(AdminServiceError, match="trùng phòng"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-02",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 3,
                "end_period": 5,
            })


def test_admin_delete_course_class_without_enrollment_success(app):
    with app.app_context():
        course, semester, room = create_base_data()

        course_class = create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-01",
            "max_students": 50,
            "status": "OPEN",
            "room_id": room.id,
            "day_of_week": 2,
            "start_period": 1,
            "end_period": 3,
        })

        delete_course_class(course_class.id)

        assert db.session.get(CourseClass, course_class.id) is None
        assert ClassSchedule.query.filter_by(course_class_id=course_class.id).count() == 0


def test_admin_delete_course_class_with_enrollment_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        course_class = create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-01",
            "max_students": 50,
            "status": "OPEN",
            "room_id": room.id,
            "day_of_week": 2,
            "start_period": 1,
            "end_period": 3,
        })

        user = User()
        user.username = "student01"
        user.password_hash = generate_password_hash("123456")
        user.role = UserRole.STUDENT
        user.is_active_account = True
        db.session.add(user)
        db.session.commit()

        student = Student(
            user_id=user.id,
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

        with pytest.raises(AdminServiceError, match="Không được xoá lớp"):
            delete_course_class(course_class.id)