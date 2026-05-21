from werkzeug.security import generate_password_hash
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
    Enrollment,
    EnrollmentStatus,
    Room,
    MajorRegistrationWindow,
)


def create_user(username, password="123456", role=UserRole.STUDENT, active=True):
    user = User()
    user.username = username
    user.password_hash = generate_password_hash(password)
    user.role = role
    user.is_active_account = active
    db.session.add(user)
    db.session.flush()
    return user


def create_student_for_user(user, code="SC01", major=None):
    student = Student(user_id=user.id, student_code=code, full_name="Test", major=major)
    db.session.add(student)
    db.session.commit()
    return student


def login(client, username, password="123456"):
    return client.post("/login", data={"username": username, "password": password})


def create_semester():
    today = date.today()
    sem = Semester(
        name="S1",
        academic_year="2026",
        start_date=today,
        end_date=today + timedelta(days=100),
        registration_start_date=today - timedelta(days=10),
        registration_end_date=today + timedelta(days=10),
        is_active=True,
    )
    db.session.add(sem)
    db.session.commit()
    return sem


def create_course_and_class(code="CR01", semester=None, class_code_suffix="01", max_students=50, current_students=0):
    course = Course(code=code, name="C", credits=3)
    db.session.add(course)
    db.session.flush()

    course_class = CourseClass(course_id=course.id, semester_id=semester.id, class_code=f"{code}-{class_code_suffix}", max_students=max_students, current_students=current_students)
    db.session.add(course_class)
    db.session.commit()
    return course, course_class


def add_enrollment(student, course_class, semester, status=EnrollmentStatus.REGISTERED):
    enrollment = Enrollment(student_id=student.id, course_class_id=course_class.id, semester_id=semester.id, status=status)
    db.session.add(enrollment)
    if status == EnrollmentStatus.REGISTERED:
        course_class.current_students = (course_class.current_students or 0) + 1
    db.session.commit()
    return enrollment


def set_pending_cancel_ids(client, enrollment_ids):
    with client.session_transaction() as sess:
        sess["pending_cancel_ids"] = list(enrollment_ids)


def test_route_guest_redirects_to_login(client):
    response = client.get("/student/classes", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location


def test_route_admin_forbidden(app, client):
    with app.app_context():
        admin = create_user("adminx", role=UserRole.ADMIN)
        create_student_for_user(admin, code="ADMINST")  # not used but safe

    login(client, "adminx")

    response = client.get("/student/classes")
    assert response.status_code == 403


def test_route_student_get_classes_ok(app, client):
    with app.app_context():
        user = create_user("studentx")
        create_student_for_user(user, code="STX")

    login(client, "studentx")

    response = client.get("/student/classes")
    assert response.status_code == 200


def test_class_list_title_shows_active_semester(app, client):
    with app.app_context():
        user = create_user("studenttitle")
        create_student_for_user(user, code="STT")

    login(client, "studenttitle")

    response = client.get("/student/classes")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    # Expect the page title/header to include "Đăng ký học phần"
    assert "Đăng ký học phần" in text


def test_route_student_get_classes_shows_expired_notice_and_hides_rows(app, client):
    with app.app_context():
        user = create_user("studentexpiredmajor")
        create_student_for_user(user, code="SEM", major="Business Administration")
        semester = create_semester()
        course, course_class = create_course_and_class(code="MJR01", semester=semester)

        window = MajorRegistrationWindow(
            semester_id=semester.id,
            major="Business Administration",
            registration_start_date=date.today() - timedelta(days=20),
            registration_end_date=date.today() - timedelta(days=1),
        )
        db.session.add(window)
        db.session.commit()

        class_code = course_class.class_code

    login(client, "studentexpiredmajor")

    response = client.get("/student/classes")
    assert response.status_code == 200
    assert "Đã hết hạn đăng ký học phần" in response.get_data(as_text=True)
    assert class_code not in response.get_data(as_text=True)


def test_route_student_post_register_success(app, client):
    with app.app_context():
        user = create_user("studentreg")
        student = create_student_for_user(user, code="SR")
        semester = create_semester()
        course, course_class = create_course_and_class(code="REG01", semester=semester)
        course_class_id = course_class.id
        student_id = student.id

    login(client, "studentreg")

    response = client.post(f"/student/classes/{course_class_id}/register", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location


def test_route_student_post_register_full_class(app, client):
    with app.app_context():
        user = create_user("studentfull")
        student = create_student_for_user(user, code="SF")
        semester = create_semester()
        course, course_class = create_course_and_class(code="FULL01", semester=semester, max_students=1, current_students=1)
        course_class_id = course_class.id
        student_id = student.id

    login(client, "studentfull")

    response = client.post(f"/student/classes/{course_class_id}/register", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location

    # ensure no enrollment created for this student
    with app.app_context():
        en = Enrollment.query.filter_by(student_id=student_id, course_class_id=course_class_id).first()
        assert en is None


def test_route_student_post_register_conflict(app, client):
    with app.app_context():
        user = create_user("studentconf")
        student = create_student_for_user(user, code="SCF")
        semester = create_semester()

        # create room
        room = Room(code="RR1", capacity=50)
        db.session.add(room)
        db.session.commit()

        # class A
        course_a, class_a = create_course_and_class(code="CF-A", semester=semester)
        sched_a = ClassSchedule(course_class_id=class_a.id, room_id=room.id, day_of_week=3, start_period=1, end_period=3)
        db.session.add(sched_a)

        # class B overlapping
        course_b, class_b = create_course_and_class(code="CF-B", semester=semester)
        sched_b = ClassSchedule(course_class_id=class_b.id, room_id=room.id, day_of_week=3, start_period=3, end_period=5)
        db.session.add(sched_b)
        db.session.commit()

        # enroll student in class_a
        en = Enrollment(student_id=student.id, course_class_id=class_a.id, semester_id=semester.id, status=EnrollmentStatus.REGISTERED)
        db.session.add(en)
        class_a.current_students = (class_a.current_students or 0) + 1
        db.session.commit()
        class_b_id = class_b.id
        student_id = student.id

    login(client, "studentconf")

    response = client.post(f"/student/classes/{class_b_id}/register", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location

    with app.app_context():
        en_b = Enrollment.query.filter_by(student_id=student_id, course_class_id=class_b_id).first()
        assert en_b is None


def test_route_student_post_register_before_registration_start(app, client):
    with app.app_context():
        user = create_user("studentfuture")
        student = create_student_for_user(user, code="SFU")
        student_id = student.id
        today = date.today()
        semester = Semester(
            name="FUTURE",
            academic_year="2026",
            start_date=today + timedelta(days=30),
            end_date=today + timedelta(days=200),
            registration_start_date=today + timedelta(days=5),
            registration_end_date=today + timedelta(days=20),
            is_active=True,
        )
        db.session.add(semester)
        db.session.flush()
        course, course_class = create_course_and_class(code="FUT01", semester=semester)
        class_id = course_class.id

    login(client, "studentfuture")

    response = client.post(f"/student/classes/{class_id}/register", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location

    with app.app_context():
        en = Enrollment.query.filter_by(student_id=student_id, course_class_id=class_id).first()
        assert en is None


def test_route_student_post_register_same_course_other_class(app, client):
    with app.app_context():
        user = create_user("studentsamecourse")
        student = create_student_for_user(user, code="SSC")
        student_id = student.id
        semester = create_semester()

        course = Course(code="SAME01", name="Same Course", credits=3)
        db.session.add(course)
        db.session.flush()

        class_a = CourseClass(course_id=course.id, semester_id=semester.id, class_code="SAME01-A", max_students=50, current_students=0)
        class_b = CourseClass(course_id=course.id, semester_id=semester.id, class_code="SAME01-B", max_students=50, current_students=0)
        db.session.add_all([class_a, class_b])
        db.session.flush()

        room = Room(code="R2", capacity=50)
        db.session.add(room)
        db.session.flush()
        db.session.add_all([
            ClassSchedule(course_class_id=class_a.id, room_id=room.id, day_of_week=2, start_period=1, end_period=3),
            ClassSchedule(course_class_id=class_b.id, room_id=room.id, day_of_week=4, start_period=1, end_period=3),
        ])

        enrollment = Enrollment(
            student_id=student.id,
            course_class_id=class_a.id,
            semester_id=semester.id,
            status=EnrollmentStatus.REGISTERED,
        )
        db.session.add(enrollment)
        class_a.current_students = (class_a.current_students or 0) + 1
        db.session.commit()
        class_b_id = class_b.id

    login(client, "studentsamecourse")

    response = client.post(f"/student/classes/{class_b_id}/register", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location

    with app.app_context():
        en_b = Enrollment.query.filter_by(student_id=student_id, course_class_id=class_b_id).first()
        assert en_b is None


def test_route_student_cancel_draft_guest_redirects_to_login(client):
    response = client.post("/student/enrollments/1/cancel-draft", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location


def test_route_student_cancel_draft_admin_forbidden(app, client):
    with app.app_context():
        admin = create_user("admin-cancel-draft", role=UserRole.ADMIN)
        create_student_for_user(admin, code="ADMINCD")

    login(client, "admin-cancel-draft")

    response = client.post("/student/enrollments/1/cancel-draft")
    assert response.status_code == 403


def test_route_student_cancel_draft_success_sets_session_and_keeps_db(app, client):
    with app.app_context():
        user = create_user("student-cancel-draft")
        student = create_student_for_user(user, code="SCD")
        semester = create_semester()
        course, course_class = create_course_and_class(code="CD01", semester=semester)
        enrollment = add_enrollment(student, course_class, semester)
        enrollment_id = enrollment.id

    login(client, "student-cancel-draft")

    response = client.post(f"/student/enrollments/{enrollment_id}/cancel-draft", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location

    with client.session_transaction() as sess:
        assert enrollment_id in sess.get("pending_cancel_ids", [])

    with app.app_context():
        refreshed = db.session.get(Enrollment, enrollment_id)
        assert refreshed.status == EnrollmentStatus.REGISTERED


def test_route_student_cancel_draft_remove_success(app, client):
    with app.app_context():
        user = create_user("student-remove-draft")
        student = create_student_for_user(user, code="SRD")
        semester = create_semester()
        course, course_class = create_course_and_class(code="CD02", semester=semester)
        enrollment = add_enrollment(student, course_class, semester)
        enrollment_id = enrollment.id

    login(client, "student-remove-draft")
    set_pending_cancel_ids(client, [enrollment_id])

    response = client.post(f"/student/enrollments/{enrollment_id}/cancel-draft/remove", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location

    with client.session_transaction() as sess:
        assert enrollment_id not in sess.get("pending_cancel_ids", [])

    with app.app_context():
        refreshed = db.session.get(Enrollment, enrollment_id)
        assert refreshed.status == EnrollmentStatus.REGISTERED


def test_route_student_confirm_registration_with_pending_cancel_success(app, client):
    with app.app_context():
        user = create_user("student-confirm-ok")
        student = create_student_for_user(user, code="SCO")
        semester = create_semester()
        course_a, class_a = create_course_and_class(code="CRA", semester=semester)
        course_b, class_b = create_course_and_class(code="CRB", semester=semester)
        course_c = Course(code="CRC", name="C", credits=9)
        db.session.add(course_c)
        db.session.flush()
        class_c = CourseClass(course_id=course_c.id, semester_id=semester.id, class_code="CRC-01", max_students=50, current_students=0)
        db.session.add(class_c)
        db.session.commit()

        en_keep1 = add_enrollment(student, class_a, semester)
        class_a.course.credits = 6
        db.session.commit()
        en_keep2 = add_enrollment(student, class_b, semester)
        class_b.course.credits = 6
        db.session.commit()
        en_cancel = add_enrollment(student, class_c, semester)
        en_keep1_id = en_keep1.id
        en_keep2_id = en_keep2.id
        en_cancel_id = en_cancel.id

    login(client, "student-confirm-ok")
    set_pending_cancel_ids(client, [en_cancel_id])

    response = client.post("/student/enrollments/confirm", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location

    with client.session_transaction() as sess:
        assert sess.get("pending_cancel_ids") is None

    with app.app_context():
        refreshed_cancel = db.session.get(Enrollment, en_cancel_id)
        refreshed_keep1 = db.session.get(Enrollment, en_keep1_id)
        refreshed_keep2 = db.session.get(Enrollment, en_keep2_id)
        assert refreshed_cancel.status == EnrollmentStatus.CANCELLED
        assert refreshed_keep1.status == EnrollmentStatus.REGISTERED
        assert refreshed_keep2.status == EnrollmentStatus.REGISTERED


def test_route_student_confirm_registration_below_minimum_keeps_session(app, client):
    with app.app_context():
        user = create_user("student-confirm-low")
        student = create_student_for_user(user, code="SCL")
        semester = create_semester()
        course_a = Course(code="CLA", name="A", credits=6)
        course_b = Course(code="CLB", name="B", credits=5)
        course_c = Course(code="CLC", name="C", credits=3)
        db.session.add_all([course_a, course_b, course_c])
        db.session.flush()
        class_a = CourseClass(course_id=course_a.id, semester_id=semester.id, class_code="CLA-01", max_students=50, current_students=0)
        class_b = CourseClass(course_id=course_b.id, semester_id=semester.id, class_code="CLB-01", max_students=50, current_students=0)
        class_c = CourseClass(course_id=course_c.id, semester_id=semester.id, class_code="CLC-01", max_students=50, current_students=0)
        db.session.add_all([class_a, class_b, class_c])
        db.session.commit()

        en_a = add_enrollment(student, class_a, semester)
        en_b = add_enrollment(student, class_b, semester)
        en_c = add_enrollment(student, class_c, semester)
        en_c_id = en_c.id

    login(client, "student-confirm-low")
    set_pending_cancel_ids(client, [en_c_id])

    response = client.post("/student/enrollments/confirm", follow_redirects=False)
    assert response.status_code == 302
    assert "/student/classes" in response.location

    with client.session_transaction() as sess:
        assert en_c_id in sess.get("pending_cancel_ids", [])

    with app.app_context():
        refreshed_c = db.session.get(Enrollment, en_c_id)
        assert refreshed_c.status == EnrollmentStatus.REGISTERED


def test_route_student_confirm_registration_overdue_cancel_shows_error_and_keeps_other_cancels(app, client):
    with app.app_context():
        user = create_user("student-confirm-overdue")
        student = create_student_for_user(user, code="SCOF")
        today = date.today()
        # Make start_date sufficiently in the past so start_date + 14 days < today
        semester = Semester(
            name="S2",
            academic_year="2026",
            start_date=today - timedelta(days=20),
            end_date=today + timedelta(days=100),
            registration_start_date=today - timedelta(days=10),
            registration_end_date=today + timedelta(days=10),
            is_active=True,
        )
        db.session.add(semester)
        db.session.flush()
        course_a = Course(code="O1", name="Overdue 1", credits=6)
        course_b = Course(code="O2", name="Overdue 2", credits=6)
        course_c = Course(code="O3", name="Overdue 3", credits=3)
        db.session.add_all([course_a, course_b, course_c])
        db.session.flush()
        class_a = CourseClass(course_id=course_a.id, semester_id=semester.id, class_code="O1-01", max_students=50, current_students=0)
        class_b = CourseClass(course_id=course_b.id, semester_id=semester.id, class_code="O2-01", max_students=50, current_students=0)
        class_c = CourseClass(course_id=course_c.id, semester_id=semester.id, class_code="O3-01", max_students=50, current_students=0)
        db.session.add_all([class_a, class_b, class_c])
        db.session.commit()

        en_a = add_enrollment(student, class_a, semester)
        en_b = add_enrollment(student, class_b, semester)
        en_c = add_enrollment(student, class_c, semester)
        en_c_id = en_c.id

    login(client, "student-confirm-overdue")
    set_pending_cancel_ids(client, [en_c_id])

    response = client.post("/student/enrollments/confirm", follow_redirects=True)
    assert response.status_code == 200

    with client.session_transaction() as sess:
        assert sess.get("pending_cancel_ids") is None

    with app.app_context():
        refreshed_c = db.session.get(Enrollment, en_c_id)
        assert refreshed_c.status == EnrollmentStatus.REGISTERED


