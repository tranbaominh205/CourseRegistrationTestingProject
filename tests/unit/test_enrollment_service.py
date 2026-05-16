import pytest
from datetime import date, timedelta

from app.extensions import db
from app.models import (
    User,
    UserRole,
    Student,
    Semester,
    Course,
    CourseClass,
    ClassSchedule,
    CompletedCourse,
    CompletedCourseStatus,
    Enrollment,
    EnrollmentStatus,
)

from app.services.enrollment_service import register_course


def create_user_and_student(username="student01"):
    user = User(username=username, password_hash="x", role=UserRole.STUDENT, is_active_account=True)
    db.session.add(user)
    db.session.flush()

    student = Student(user_id=user.id, student_code=f"SC-{username}", full_name="Test Student")
    db.session.add(student)
    db.session.commit()

    return user, student


def create_semester(start_offset=0, reg_start_offset=-10, reg_end_offset=10):
    today = date.today()
    semester = Semester(
        name="TS",
        start_date=today + timedelta(days=start_offset),
        registration_start_date=today + timedelta(days=reg_start_offset),
        registration_end_date=today + timedelta(days=reg_end_offset),
        cancel_deadline=today + timedelta(days=reg_end_offset + 30),
        is_active=True,
    )
    db.session.add(semester)
    db.session.commit()
    return semester


def create_course_and_class(code="C001", credits=3, semester=None, class_code_suffix="01", max_students=50, current_students=0):
    course = Course(code=code, name="Course", credits=credits)
    db.session.add(course)
    db.session.flush()

    course_class = CourseClass(
        course_id=course.id,
        semester_id=semester.id,
        class_code=f"{code}-{class_code_suffix}",
        max_students=max_students,
        current_students=current_students,
    )
    db.session.add(course_class)
    db.session.commit()

    return course, course_class


def add_schedule(course_class, day=1, start=1, end=3):
    schedule = ClassSchedule(course_class_id=course_class.id, room_id=1, day_of_week=day, start_period=start, end_period=end)
    db.session.add(schedule)
    db.session.commit()
    return schedule


def add_completed_course(student, course, semester, status=CompletedCourseStatus.PASSED):
    cc = CompletedCourse(student_id=student.id, course_id=course.id, semester_id=semester.id, final_score=8.0, status=status)
    db.session.add(cc)
    db.session.commit()
    return cc


def add_enrollment(student, course_class, semester):
    en = Enrollment(student_id=student.id, course_class_id=course_class.id, semester_id=semester.id, status=EnrollmentStatus.REGISTERED)
    db.session.add(en)
    # increment current_students
    try:
        course_class.current_students = (course_class.current_students or 0) + 1
    except Exception:
        pass
    db.session.commit()
    return en


def test_enroll_success(app):
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()
        course, course_class = create_course_and_class(code="ENR01", semester=semester)

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert error is None
        assert enrollment is not None
        assert enrollment.student_id == student.id


def test_enroll_class_not_found(app):
    with app.app_context():
        user, student = create_user_and_student()

        enrollment, error = register_course(student.id, 9999, current_date=date.today())

        assert enrollment is None
        assert error == "Không tìm thấy lớp học phần"


def test_enroll_expired_registration(app):
    with app.app_context():
        user, student = create_user_and_student()
        # semester with registration end in the past
        semester = create_semester(reg_start_offset=-30, reg_end_offset=-1)
        course, course_class = create_course_and_class(code="ENR02", semester=semester)

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert enrollment is None
        assert error == "Đã hết hạn đăng ký học phần"


def test_enroll_before_registration_start_allowed(app):
    # current implementation does not block before registration_start_date
    with app.app_context():
        user, student = create_user_and_student()
        # registration starts in future
        semester = create_semester(reg_start_offset=5, reg_end_offset=30)
        course, course_class = create_course_and_class(code="ENR03", semester=semester)

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        # expected: allowed by current logic
        assert error is None
        assert enrollment is not None


def test_enroll_class_full(app):
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()
        course, course_class = create_course_and_class(code="ENR04", semester=semester, max_students=1, current_students=1)

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert enrollment is None
        assert error == "Lớp học phần đã đủ số lượng"


def test_enroll_already_registered_same_class(app):
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()
        course, course_class = create_course_and_class(code="ENR05", semester=semester)

        add_enrollment(student, course_class, semester)

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert enrollment is None
        assert error == "Sinh viên đã đăng ký lớp học phần này"


def test_enroll_registered_same_course_different_class_allowed(app):
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()
        course = Course(code="ENR06", name="C", credits=3)
        db.session.add(course)
        db.session.flush()

        class1 = CourseClass(course_id=course.id, semester_id=semester.id, class_code="ENR06-01", max_students=50, current_students=0)
        class2 = CourseClass(course_id=course.id, semester_id=semester.id, class_code="ENR06-02", max_students=50, current_students=0)
        db.session.add_all([class1, class2])
        db.session.commit()

        add_enrollment(student, class1, semester)

        enrollment, error = register_course(student.id, class2.id, current_date=date.today())

        # current logic allows registering same course in different class
        assert error is None
        assert enrollment is not None


def test_enroll_already_completed_course(app):
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()
        course, course_class = create_course_and_class(code="ENR07", semester=semester)

        add_completed_course(student, course, semester)

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert enrollment is None
        assert error == "Sinh viên đã học môn này rồi"


def test_enroll_schedule_conflict(app):
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create existing class with schedule day 2, periods 1-3
        course_a, class_a = create_course_and_class(code="ENR08A", semester=semester)
        # create target class overlapping day 2, periods 3-5 (overlap at period 3)
        course_b, class_b = create_course_and_class(code="ENR08B", semester=semester)

        # create a dummy room for schedules
        from app.models import Room
        room = Room(code="R1", capacity=50)
        db.session.add(room)
        db.session.flush()

        sched_a = ClassSchedule(course_class_id=class_a.id, room_id=room.id, day_of_week=2, start_period=1, end_period=3)
        sched_b = ClassSchedule(course_class_id=class_b.id, room_id=room.id, day_of_week=2, start_period=3, end_period=5)
        db.session.add_all([sched_a, sched_b])
        db.session.commit()

        # enroll student into class_a
        add_enrollment(student, class_a, semester)

        enrollment, error = register_course(student.id, class_b.id, current_date=date.today())

        assert enrollment is None
        assert error == "Lớp học phần bị trùng lịch học"


def test_enroll_increments_current_students(app):
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()
        course, course_class = create_course_and_class(code="ENR09", semester=semester, current_students=0)

        before = course_class.current_students
        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert error is None
        assert enrollment is not None

        refreshed = db.session.get(CourseClass, course_class.id)
        assert refreshed.current_students == before + 1

