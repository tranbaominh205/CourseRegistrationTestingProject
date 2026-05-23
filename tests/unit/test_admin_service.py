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


def test_admin_create_course_class_duplicate_code_fail(app):
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

        with pytest.raises(AdminServiceError, match="đã tồn tại"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 3,
                "start_period": 4,
                "end_period": 6,
            })


def test_admin_create_course_class_same_room_different_time_success(app):
    with app.app_context():
        course, semester, room = create_base_data()

        course_class_1 = create_course_class({
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

        course_class_2 = create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-02",
            "max_students": 50,
            "status": "OPEN",
            "room_id": room.id,
            "day_of_week": 2,
            "start_period": 4,
            "end_period": 6,
        })

        assert course_class_1.id is not None
        assert course_class_2.id is not None
        assert course_class_1.schedules[0].room_id == room.id
        assert course_class_2.schedules[0].room_id == room.id


def test_admin_create_course_class_same_time_different_room_success(app):
    with app.app_context():
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

        course_class_1 = create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-01",
            "max_students": 50,
            "status": "OPEN",
            "room_id": room_a.id,
            "day_of_week": 2,
            "start_period": 1,
            "end_period": 3,
        })

        course_class_2 = create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-02",
            "max_students": 40,
            "status": "OPEN",
            "room_id": room_b.id,
            "day_of_week": 2,
            "start_period": 1,
            "end_period": 3,
        })

        assert course_class_1.id is not None
        assert course_class_2.id is not None
        assert course_class_1.schedules[0].room_id == room_a.id
        assert course_class_2.schedules[0].room_id == room_b.id


def test_admin_create_course_class_empty_class_code_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Mã lớp học phần không được để trống"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_whitespace_class_code_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Mã lớp học phần không được để trống"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "   ",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_invalid_status_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Trạng thái lớp học phần không hợp lệ"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "INVALID_STATUS",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_invalid_day_of_week_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Thứ học phải từ 2 đến 8"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 1,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_invalid_day_of_week_over_8_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Thứ học phải từ 2 đến 8"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 9,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_invalid_start_period_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Tiết học phải từ 1 đến 15"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 0,
                "end_period": 3,
            })


def test_admin_create_course_class_invalid_end_period_over_15_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Tiết học phải từ 1 đến 15"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 16,
            })


def test_admin_create_course_class_start_period_greater_than_end_period_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Tiết bắt đầu không được lớn hơn tiết kết thúc"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 5,
                "end_period": 3,
            })


def test_admin_create_course_class_nonexistent_course_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Môn học không tồn tại"):
            create_course_class({
                "course_id": 9999,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_nonexistent_semester_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Học kỳ không tồn tại"):
            create_course_class({
                "course_id": course.id,
                "semester_id": 9999,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_nonexistent_room_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Phòng học không tồn tại"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": 9999,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_max_students_exceeds_room_capacity_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        small_room = Room(code="C301", capacity=30)
        db.session.add(small_room)
        db.session.commit()

        with pytest.raises(AdminServiceError, match="Số sinh viên tối đa không được vượt quá sức chứa phòng"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01B",
                "max_students": 40,
                "status": "OPEN",
                "room_id": small_room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_invalid_max_students_zero_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Số sinh viên tối đa mỗi lớp không được vượt quá 50"):
            create_course_class({
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": -1,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_create_course_class_invalid_course_id_type_fail(app):
    with app.app_context():
        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Môn học không hợp lệ"):
            create_course_class({
                "course_id": "invalid",
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 50,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_delete_course_class_not_found_fail(app):
    with app.app_context():
        from app.services.admin_service import delete_course_class

        with pytest.raises(AdminServiceError, match="Không tìm thấy lớp học phần"):
            delete_course_class(9999)


def test_admin_update_course_class_success(app):
    with app.app_context():
        from app.services.admin_service import update_course_class

        course, semester, room = create_base_data()

        course_class = create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-01",
            "max_students": 30,
            "status": "OPEN",
            "room_id": room.id,
            "day_of_week": 2,
            "start_period": 1,
            "end_period": 3,
        })

        updated_class = update_course_class(course_class.id, {
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-01-V2",
            "max_students": 40,
            "status": "OPEN",
            "room_id": room.id,
            "day_of_week": 3,
            "start_period": 4,
            "end_period": 6,
        })

        assert updated_class.class_code == "IT001-01-V2"
        assert updated_class.max_students == 40
        assert updated_class.schedules[0].day_of_week == 3


def test_admin_update_course_class_not_found_fail(app):
    with app.app_context():
        from app.services.admin_service import update_course_class

        course, semester, room = create_base_data()

        with pytest.raises(AdminServiceError, match="Không tìm thấy lớp học phần"):
            update_course_class(9999, {
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 40,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })


def test_admin_update_course_class_reduce_max_students_below_current_fail(app):
    with app.app_context():
        from app.services.admin_service import update_course_class

        course, semester, room = create_base_data()

        course_class = create_course_class({
            "course_id": course.id,
            "semester_id": semester.id,
            "class_code": "IT001-01",
            "max_students": 30,
            "status": "OPEN",
            "room_id": room.id,
            "day_of_week": 2,
            "start_period": 1,
            "end_period": 3,
        })

        course_class.current_students = 25
        db.session.commit()

        with pytest.raises(AdminServiceError, match="Số sinh viên tối đa không được nhỏ hơn số sinh viên hiện tại"):
            update_course_class(course_class.id, {
                "course_id": course.id,
                "semester_id": semester.id,
                "class_code": "IT001-01",
                "max_students": 20,
                "status": "OPEN",
                "room_id": room.id,
                "day_of_week": 2,
                "start_period": 1,
                "end_period": 3,
            })
