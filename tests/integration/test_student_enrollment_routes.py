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
)


def create_user(username, password="123456", role=UserRole.STUDENT, active=True):
    user = User(username=username, password_hash=generate_password_hash(password), role=role, is_active_account=active)
    db.session.add(user)
    db.session.flush()
    return user


def create_student_for_user(user, code="SC01"):
    student = Student(user_id=user.id, student_code=code, full_name="Test")
    db.session.add(student)
    db.session.commit()
    return student


def login(client, username, password="123456"):
    return client.post("/login", data={"username": username, "password": password})


def create_semester():
    today = date.today()
    sem = Semester(
        name="S1",
        start_date=today,
        registration_start_date=today - timedelta(days=10),
        registration_end_date=today + timedelta(days=10),
        cancel_deadline=today + timedelta(days=30),
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

