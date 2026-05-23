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
    MajorRegistrationWindow,
)

from app.services.enrollment_service import register_course
from app.services.enrollment_service import (
    validate_cancel_draft,
    calculate_credits_after_pending_cancel,
    cancel_pending_enrollments,
    can_cancel_enrollment,
)


def create_user_and_student(username="student01", major=None):
    user = User()
    user.username = username
    user.password_hash = "x"
    user.role = UserRole.STUDENT
    user.is_active_account = True
    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        student_code=f"SC-{username}",
        full_name="Test Student",
        major=major,
    )
    db.session.add(student)
    db.session.commit()

    return user, student


def create_semester(start_offset=0, reg_start_offset=-10, reg_end_offset=10):
    today = date.today()
    semester = Semester(
        name="TS",
        academic_year="2026",
        start_date=today + timedelta(days=start_offset),
        end_date=today + timedelta(days=start_offset + 100),
        registration_start_date=today + timedelta(days=reg_start_offset),
        registration_end_date=today + timedelta(days=reg_end_offset),
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
        semester = create_semester(reg_start_offset=-30, reg_end_offset=-1)
        course, course_class = create_course_and_class(code="ENR02", semester=semester)

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert enrollment is None
        assert error == "Đã hết hạn đăng ký học phần"


def test_enroll_before_registration_start_blocked(app):
    with app.app_context():
        user, student = create_user_and_student()
        semester = create_semester(reg_start_offset=5, reg_end_offset=30)
        course, course_class = create_course_and_class(code="ENR03", semester=semester)

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert enrollment is None
        assert error == "Chưa đến thời gian đăng ký học phần"


def test_enroll_expired_major_window_blocks_even_when_semester_open(app):
    with app.app_context():
        user, student = create_user_and_student(username="expired-major", major="Business Administration")
        semester = create_semester(reg_start_offset=-10, reg_end_offset=10)
        course, course_class = create_course_and_class(code="ENR10", semester=semester)

        db.session.add(MajorRegistrationWindow(
            semester_id=semester.id,
            major="Business Administration",
            registration_start_date=date.today() - timedelta(days=30),
            registration_end_date=date.today() - timedelta(days=1),
        ))
        db.session.commit()

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert enrollment is None
        assert error == "Đã hết hạn đăng ký học phần"


def test_enroll_future_major_window_blocks_even_when_semester_open(app):
    with app.app_context():
        user, student = create_user_and_student(username="future-major", major="Digital Design")
        semester = create_semester(reg_start_offset=-10, reg_end_offset=10)
        course, course_class = create_course_and_class(code="ENR11", semester=semester)

        db.session.add(MajorRegistrationWindow(
            semester_id=semester.id,
            major="Digital Design",
            registration_start_date=date.today() + timedelta(days=3),
            registration_end_date=date.today() + timedelta(days=20),
        ))
        db.session.commit()

        enrollment, error = register_course(student.id, course_class.id, current_date=date.today())

        assert enrollment is None
        assert error == "Chưa đến thời gian đăng ký học phần"


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


def test_enroll_registered_same_course_different_class_blocked(app):
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

        assert enrollment is None
        assert error == "Sinh viên đã đăng ký môn học này ở lớp khác"


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

        course_a, class_a = create_course_and_class(code="ENR08A", semester=semester)
        course_b, class_b = create_course_and_class(code="ENR08B", semester=semester)

        from app.models import Room
        room = Room(code="R1", capacity=50)
        db.session.add(room)
        db.session.flush()

        sched_a = ClassSchedule(course_class_id=class_a.id, room_id=room.id, day_of_week=2, start_period=1, end_period=3)
        sched_b = ClassSchedule(course_class_id=class_b.id, room_id=room.id, day_of_week=2, start_period=3, end_period=5)
        db.session.add_all([sched_a, sched_b])
        db.session.commit()

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


def test_validate_cancel_draft_success(app):
    with app.app_context():
        user, student = create_user_and_student(username="cancel-ok")
        semester = create_semester()
        course, course_class = create_course_and_class(code="CXL01", semester=semester)
        enrollment = add_enrollment(student, course_class, semester)

        found, error = validate_cancel_draft(student.id, enrollment.id)

        assert error is None
        assert found is not None
        assert found.id == enrollment.id


def test_validate_cancel_draft_not_found(app):
    with app.app_context():
        user, student = create_user_and_student(username="cancel-missing")

        found, error = validate_cancel_draft(student.id, 9999)

        assert found is None
        assert error == "Không tìm thấy đăng ký học phần."


def test_validate_cancel_draft_other_student(app):
    with app.app_context():
        user_a, student_a = create_user_and_student(username="cancel-a")
        user_b, student_b = create_user_and_student(username="cancel-b")
        semester = create_semester()
        course, course_class = create_course_and_class(code="CXL02", semester=semester)
        enrollment = add_enrollment(student_a, course_class, semester)

        found, error = validate_cancel_draft(student_b.id, enrollment.id)

        assert found is None
        assert error == "Bạn không có quyền hủy đăng ký này."


def test_validate_cancel_draft_already_cancelled(app):
    with app.app_context():
        user, student = create_user_and_student(username="cancel-old")
        semester = create_semester()
        course, course_class = create_course_and_class(code="CXL03", semester=semester)
        enrollment = add_enrollment(student, course_class, semester)
        enrollment.status = EnrollmentStatus.CANCELLED
        db.session.commit()

        found, error = validate_cancel_draft(student.id, enrollment.id)

        assert found is None
        assert error == "Học phần này đã bị hủy trước đó."


def test_cancel_allowed_on_fourteenth_day_from_semester_start(app):
    with app.app_context():
        user, student = create_user_and_student(username="cancel-day14")
        today = date.today()
        semester = Semester(
            name="DAY14",
            academic_year="2026",
            start_date=today - timedelta(days=14),
            end_date=today + timedelta(days=100),
            registration_start_date=today - timedelta(days=20),
            registration_end_date=today + timedelta(days=10),
            is_active=True,
        )
        db.session.add(semester)
        db.session.commit()

        course, course_class = create_course_and_class(code="CXL14", semester=semester)
        enrollment = add_enrollment(student, course_class, semester)

        ok, error = can_cancel_enrollment(student.id, enrollment.id, current_date=today)
        cancelled_ids, messages = cancel_pending_enrollments(student.id, [enrollment.id], current_date=today)

        assert ok is True
        assert error is None
        assert messages == []
        assert cancelled_ids == [enrollment.id]


def test_cancel_blocked_after_fourteenth_day_from_semester_start(app):
    with app.app_context():
        user, student = create_user_and_student(username="cancel-day15")
        today = date.today()
        semester = Semester(
            name="DAY15",
            academic_year="2026",
            start_date=today - timedelta(days=15),
            end_date=today + timedelta(days=100),
            registration_start_date=today - timedelta(days=20),
            registration_end_date=today + timedelta(days=10),
            is_active=True,
        )
        db.session.add(semester)
        db.session.commit()

        course, course_class = create_course_and_class(code="CXL15", semester=semester)
        enrollment = add_enrollment(student, course_class, semester)

        ok, error = can_cancel_enrollment(student.id, enrollment.id, current_date=today)
        cancelled_ids, messages = cancel_pending_enrollments(student.id, [enrollment.id], current_date=today)

        assert ok is False
        assert error == "Đã quá hạn hủy đăng ký học phần."
        assert cancelled_ids == []
        assert messages == ["Đã quá hạn hủy đăng ký học phần."]


def test_calculate_credits_after_pending_cancel_no_pending(app):
    with app.app_context():
        user, student = create_user_and_student(username="credit-none")
        semester = create_semester()
        course_a, class_a = create_course_and_class(code="CRED01", credits=3, semester=semester)
        course_b, class_b = create_course_and_class(code="CRED02", credits=4, semester=semester)
        add_enrollment(student, class_a, semester)
        add_enrollment(student, class_b, semester)

        total = calculate_credits_after_pending_cancel(student.id, semester.id, [])

        assert total == 7


def test_calculate_credits_after_pending_cancel_one_pending(app):
    with app.app_context():
        user, student = create_user_and_student(username="credit-one")
        semester = create_semester()
        course_a, class_a = create_course_and_class(code="CRED03", credits=3, semester=semester)
        course_b, class_b = create_course_and_class(code="CRED04", credits=4, semester=semester)
        en_a = add_enrollment(student, class_a, semester)
        add_enrollment(student, class_b, semester)

        total = calculate_credits_after_pending_cancel(student.id, semester.id, [en_a.id])

        assert total == 4


def test_calculate_credits_after_pending_cancel_many_pending_and_invalid_ids(app):
    with app.app_context():
        user, student = create_user_and_student(username="credit-many")
        semester = create_semester()
        course_a, class_a = create_course_and_class(code="CRED05", credits=3, semester=semester)
        course_b, class_b = create_course_and_class(code="CRED06", credits=4, semester=semester)
        course_c, class_c = create_course_and_class(code="CRED07", credits=5, semester=semester)
        en_a = add_enrollment(student, class_a, semester)
        en_b = add_enrollment(student, class_b, semester)
        add_enrollment(student, class_c, semester)

        total = calculate_credits_after_pending_cancel(student.id, semester.id, [en_a.id, en_b.id, 9999, "bad-id"])

        assert total == 5


def test_cancel_pending_enrollments_success_and_current_students_not_negative(app):
    with app.app_context():
        user, student = create_user_and_student(username="cancel-batch")
        semester = create_semester()
        course_a, class_a = create_course_and_class(code="CXL10A", credits=3, semester=semester, current_students=0)
        course_b, class_b = create_course_and_class(code="CXL10B", credits=4, semester=semester, current_students=0)
        en_a = add_enrollment(student, class_a, semester)
        en_b = add_enrollment(student, class_b, semester)

        cancelled_ids, messages = cancel_pending_enrollments(student.id, [en_a.id, en_b.id])

        assert messages == []
        assert set(cancelled_ids) == {en_a.id, en_b.id}

        refreshed_a = db.session.get(Enrollment, en_a.id)
        refreshed_b = db.session.get(Enrollment, en_b.id)
        refreshed_class_a = db.session.get(CourseClass, class_a.id)
        refreshed_class_b = db.session.get(CourseClass, class_b.id)

        assert refreshed_a.status == EnrollmentStatus.CANCELLED
        assert refreshed_b.status == EnrollmentStatus.CANCELLED
        assert refreshed_class_a.current_students == 0
        assert refreshed_class_b.current_students == 0


def test_cancel_pending_enrollments_after_deadline_and_midterm_blocked(app):
    with app.app_context():
        user, student = create_user_and_student(username="cancel-blocked")
        today = date.today()
        semester = Semester(
            name="BLOCK",
            academic_year="2026",
            start_date=today,
            end_date=today + timedelta(days=100),
            registration_start_date=today - timedelta(days=10),
            registration_end_date=today + timedelta(days=10),
            is_active=True,
        )
        db.session.add(semester)
        db.session.commit()

        course_a, class_a = create_course_and_class(code="CXL11", credits=3, semester=semester, current_students=1)
        enrollment = add_enrollment(student, class_a, semester)
        enrollment.midterm_score = 8.0
        db.session.commit()

        cancelled_ids, messages = cancel_pending_enrollments(student.id, [enrollment.id])

        assert cancelled_ids == []
        assert "hủy" in messages[0].lower()

        refreshed = db.session.get(Enrollment, enrollment.id)
        refreshed_class = db.session.get(CourseClass, class_a.id)
        assert refreshed.status == EnrollmentStatus.REGISTERED
        assert refreshed_class.current_students == 2


def test_cancel_pending_enrollments_midterm_blocked(app):
    with app.app_context():
        user, student = create_user_and_student(username="cancel-midterm")
        semester = create_semester()
        course_a, class_a = create_course_and_class(code="CXL12", credits=3, semester=semester, current_students=0)
        enrollment = add_enrollment(student, class_a, semester)
        enrollment.midterm_score = 7.5
        db.session.commit()

        cancelled_ids, messages = cancel_pending_enrollments(student.id, [enrollment.id])

        assert cancelled_ids == []
        assert any("giữa kỳ" in message.lower() for message in messages)

        refreshed = db.session.get(Enrollment, enrollment.id)
        refreshed_class = db.session.get(CourseClass, class_a.id)
        assert refreshed.status == EnrollmentStatus.REGISTERED
        assert refreshed_class.current_students == 1


def test_re_register_after_cancel_reactivates_old_enrollment(app):
    with app.app_context():
        from app.services.enrollment_service import cancel_pending_enrollments
        
        user, student = create_user_and_student(username="reregister-test")
        semester = create_semester()
        course, course_class = create_course_and_class(code="REREG01", semester=semester, current_students=0)

        enrollment_1, error_1 = register_course(student.id, course_class.id, current_date=date.today())
        assert error_1 is None
        assert enrollment_1 is not None
        initial_id = enrollment_1.id
        
        refreshed_class = db.session.get(CourseClass, course_class.id)
        assert refreshed_class.current_students == 1

        cancelled_ids, cancel_messages = cancel_pending_enrollments(
            student.id, 
            [enrollment_1.id],
            current_date=date.today()
        )
        assert cancelled_ids == [initial_id]
        assert cancel_messages == []
        
        cancelled_enrollment = db.session.get(Enrollment, initial_id)
        assert cancelled_enrollment.status == EnrollmentStatus.CANCELLED
        
        refreshed_class = db.session.get(CourseClass, course_class.id)
        assert refreshed_class.current_students == 0

        enrollment_2, error_2 = register_course(student.id, course_class.id, current_date=date.today())
        assert error_2 is None
        assert enrollment_2 is not None
        
        assert enrollment_2.id == initial_id
        
        refreshed_enrollment = db.session.get(Enrollment, initial_id)
        assert refreshed_enrollment.status == EnrollmentStatus.REGISTERED
        assert refreshed_enrollment.registered_at is not None
        assert refreshed_enrollment.cancelled_at is None
        
        refreshed_class = db.session.get(CourseClass, course_class.id)
        assert refreshed_class.current_students == 1
        
        all_enrollments = Enrollment.query.filter_by(
            student_id=student.id,
            course_class_id=course_class.id
        ).all()
        assert len(all_enrollments) == 1
        assert all_enrollments[0].id == initial_id
