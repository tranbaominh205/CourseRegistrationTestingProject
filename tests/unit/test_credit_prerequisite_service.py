from datetime import date, timedelta

from app.extensions import db
from app.models import (
    User,
    UserRole,
    Student,
    Semester,
    Course,
    CourseClass,
    CompletedCourse,
    CompletedCourseStatus,
    Enrollment,
    EnrollmentStatus,
    CoursePrerequisite,
)

from app.services.enrollment_service import (
    register_course,
    can_confirm_registration,
    calculate_registered_credits,
    MIN_CREDITS,
    MAX_CREDITS,
)


def create_user_and_student(username="student01"):
    user = User(username=username, password_hash="x", role=UserRole.STUDENT, is_active_account=True)
    db.session.add(user)
    db.session.flush()

    student = Student(user_id=user.id, student_code=f"SC-{username}", full_name="Test Student")
    db.session.add(student)
    db.session.commit()

    return user, student


def create_semester():
    today = date.today()
    semester = Semester(
        name="TS",
        academic_year="2026",
        start_date=today,
        end_date=today + timedelta(days=100),
        registration_start_date=today - timedelta(days=10),
        registration_end_date=today + timedelta(days=10),
        is_active=True,
    )
    db.session.add(semester)
    db.session.commit()
    return semester


def create_course(code="C001", credits=3):
    course = Course(code=code, name="Course", credits=credits)
    db.session.add(course)
    db.session.commit()
    return course


def create_course_class(course, semester, class_code_suffix="01"):
    course_class = CourseClass(
        course_id=course.id,
        semester_id=semester.id,
        class_code=f"{course.code}-{class_code_suffix}",
        max_students=50,
        current_students=0,
    )
    db.session.add(course_class)
    db.session.commit()
    return course_class


def add_enrollment(student, course_class, semester):
    en = Enrollment(
        student_id=student.id,
        course_class_id=course_class.id,
        semester_id=semester.id,
        status=EnrollmentStatus.REGISTERED,
    )
    db.session.add(en)
    course_class.current_students = (course_class.current_students or 0) + 1
    db.session.commit()
    return en


def add_completed_course(student, course, semester, final_score=8.0, status=CompletedCourseStatus.PASSED):
    cc = CompletedCourse(
        student_id=student.id,
        course_id=course.id,
        semester_id=semester.id,
        final_score=final_score,
        status=status,
    )
    db.session.add(cc)
    db.session.commit()
    return cc


def add_prerequisite(course, prerequisite_course):
    prereq = CoursePrerequisite(course_id=course.id, prerequisite_course_id=prerequisite_course.id)
    db.session.add(prereq)
    db.session.commit()
    return prereq


# =====================================================
# CREDIT TESTS
# =====================================================


def test_credit_limit_constants_are_defined():
    assert MIN_CREDITS == 12
    assert MAX_CREDITS == 25


def test_credit_confirm_zero_credits(app):
    # CREDIT_TC01: tổng tín chỉ = 0, xác nhận fail
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        can_confirm, message = can_confirm_registration(student.id, semester.id)

        assert can_confirm is False
        assert "12" in message  # chưa đủ tối thiểu 12 tín chỉ


def test_credit_confirm_11_credits(app):
    # CREDIT_TC02: tổng tín chỉ = 11, xác nhận fail
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create course 11 credits and enroll
        course_11 = create_course(code="CR11", credits=11)
        class_11 = create_course_class(course_11, semester)
        add_enrollment(student, class_11, semester)

        can_confirm, message = can_confirm_registration(student.id, semester.id)

        assert can_confirm is False
        assert "1" in message  # cần 1 tín chỉ nữa


def test_credit_confirm_12_credits_pass(app):
    # CREDIT_TC03: tổng tín chỉ = 12, xác nhận pass
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create courses totaling 12 credits
        course_c1 = create_course(code="C12A", credits=6)
        course_c2 = create_course(code="C12B", credits=6)
        class_c1 = create_course_class(course_c1, semester)
        class_c2 = create_course_class(course_c2, semester)

        add_enrollment(student, class_c1, semester)
        add_enrollment(student, class_c2, semester)

        assert calculate_registered_credits(student.id, semester.id) == 12

        can_confirm, message = can_confirm_registration(student.id, semester.id)

        assert can_confirm is True


def test_credit_confirm_25_credits_pass(app):
    # CREDIT_TC04: tổng tín chỉ = 25, xác nhận pass
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create courses totaling 25 credits
        course_c1 = create_course(code="C25A", credits=10)
        course_c2 = create_course(code="C25B", credits=10)
        course_c3 = create_course(code="C25C", credits=5)
        class_c1 = create_course_class(course_c1, semester)
        class_c2 = create_course_class(course_c2, semester)
        class_c3 = create_course_class(course_c3, semester)

        add_enrollment(student, class_c1, semester)
        add_enrollment(student, class_c2, semester)
        add_enrollment(student, class_c3, semester)

        can_confirm, message = can_confirm_registration(student.id, semester.id)

        assert can_confirm is True


def test_credit_confirm_26_credits_fail(app):
    # CREDIT_TC05: tổng tín chỉ = 26, xác nhận fail (vượt giới hạn)
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create courses totaling 26 credits
        course_c1 = create_course(code="COVER26A", credits=13)
        course_c2 = create_course(code="COVER26B", credits=13)
        class_c1 = create_course_class(course_c1, semester)
        class_c2 = create_course_class(course_c2, semester)

        add_enrollment(student, class_c1, semester)
        add_enrollment(student, class_c2, semester)

        can_confirm, message = can_confirm_registration(student.id, semester.id)

        assert can_confirm is False
        assert "vượt quá" in message.lower() or "exceed" in message.lower()


# =====================================================
# PREREQUISITE TESTS
# =====================================================


def test_prereq_no_prerequisite_can_register(app):
    # PREREQ_TC01: môn không có tiên quyết, đăng ký được
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create course with no prerequisite
        course_free = create_course(code="FREE01", credits=3)
        class_free = create_course_class(course_free, semester)

        enrollment, error = register_course(student.id, class_free.id, current_date=date.today())

        assert error is None
        assert enrollment is not None


def test_prereq_completed_prerequisite_can_register(app):
    # PREREQ_TC02: có tiên quyết và đã pass, đăng ký được
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create prerequisite course
        prereq_course = create_course(code="PREREQ01", credits=3)

        # create target course requiring prerequisite
        target_course = create_course(code="TARGET02", credits=3)
        add_prerequisite(target_course, prereq_course)

        # mark student as having completed prerequisite
        add_completed_course(student, prereq_course, semester, status=CompletedCourseStatus.PASSED)

        # now register for target course
        target_class = create_course_class(target_course, semester)
        enrollment, error = register_course(student.id, target_class.id, current_date=date.today())

        assert error is None
        assert enrollment is not None


def test_prereq_not_completed_cannot_register(app):
    # PREREQ_TC03: có tiên quyết nhưng chưa học, đăng ký fail
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create prerequisite course
        prereq_course = create_course(code="PREREQ03", credits=3)

        # create target course requiring prerequisite
        target_course = create_course(code="TARGET03", credits=3)
        add_prerequisite(target_course, prereq_course)

        # student has NOT completed prerequisite
        # try to register for target course
        target_class = create_course_class(target_course, semester)
        enrollment, error = register_course(student.id, target_class.id, current_date=date.today())

        assert enrollment is None
        assert error is not None
        assert "tiên quyết" in error.lower() or "prerequisite" in error.lower()


def test_prereq_failed_prerequisite_cannot_register(app):
    # PREREQ_TC04: có tiên quyết nhưng học FAILED, đăng ký fail
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester()

        # create prerequisite course
        prereq_course = create_course(code="PREREQ04", credits=3)

        # create target course requiring prerequisite
        target_course = create_course(code="TARGET04", credits=3)
        add_prerequisite(target_course, prereq_course)

        # mark student as having FAILED prerequisite
        add_completed_course(student, prereq_course, semester, final_score=3.0, status=CompletedCourseStatus.FAILED)

        # try to register for target course
        target_class = create_course_class(target_course, semester)
        enrollment, error = register_course(student.id, target_class.id, current_date=date.today())

        assert enrollment is None
        assert error is not None
        assert "tiên quyết" in error.lower() or "prerequisite" in error.lower()

