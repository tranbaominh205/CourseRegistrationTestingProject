from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import (
    User,
    UserRole,
    Student,
    Semester,
    Course,
    CoursePrerequisite,
    Room,
    CourseClass,
    ClassSchedule,
    CompletedCourse,
    CourseClassStatus,
    CompletedCourseStatus,
)

app = create_app()


@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")


@app.cli.command("reset-db")
def reset_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully.")


@app.cli.command("seed-data")
def seed_data():
    with app.app_context():
        # Users
        admin = User.query.filter_by(username="admin01").first()
        if admin is None:
            admin = User(
                username="admin01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.ADMIN,
                is_active_account=True
            )
            db.session.add(admin)

        student_user = User.query.filter_by(username="student01").first()
        if student_user is None:
            student_user = User(
                username="student01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.STUDENT,
                is_active_account=True
            )
            db.session.add(student_user)
            db.session.flush()

            student = Student(
                user_id=student_user.id,
                student_code="SV001",
                full_name="Nguyen Van Student",
                major="Information Technology"
            )
            db.session.add(student)

        locked_user = User.query.filter_by(username="locked01").first()
        if locked_user is None:
            locked_user = User(
                username="locked01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.STUDENT,
                is_active_account=False
            )
            db.session.add(locked_user)

        db.session.commit()

        # Semester
        semester = Semester.query.filter_by(name="HK1 2026").first()
        if semester is None:
            semester = Semester(
                name="HK1 2026",
                start_date=date(2026, 9, 1),
                registration_start_date=date(2026, 8, 1),
                registration_end_date=date(2026, 8, 25),
                cancel_deadline=date(2026, 9, 15),
                is_active=True
            )
            db.session.add(semester)

        # Courses
        course_python = Course.query.filter_by(code="ITEC1401").first()
        if course_python is None:
            course_python = Course(
                code="ITEC1401",
                name="Nhập môn lập trình",
                credits=3
            )
            db.session.add(course_python)

        course_oop = Course.query.filter_by(code="ITEC2504").first()
        if course_oop is None:
            course_oop = Course(
                code="ITEC2504",
                name="Lập trình hướng đối tượng",
                credits=4
            )
            db.session.add(course_oop)

        course_web = Course.query.filter_by(code="ITEC3401").first()
        if course_web is None:
            course_web = Course(
                code="ITEC3401",
                name="Lập trình Web",
                credits=3
            )
            db.session.add(course_web)

        course_testing = Course.query.filter_by(code="ITEC4501").first()
        if course_testing is None:
            course_testing = Course(
                code="ITEC4501",
                name="Kiểm thử phần mềm",
                credits=3
            )
            db.session.add(course_testing)

        db.session.commit()

        # Prerequisite: Lập trình Web cần đã học Lập trình hướng đối tượng
        prerequisite = CoursePrerequisite.query.filter_by(
            course_id=course_web.id,
            prerequisite_course_id=course_oop.id
        ).first()

        if prerequisite is None:
            prerequisite = CoursePrerequisite(
                course_id=course_web.id,
                prerequisite_course_id=course_oop.id
            )
            db.session.add(prerequisite)

        # Rooms
        room_a101 = Room.query.filter_by(code="A101").first()
        if room_a101 is None:
            room_a101 = Room(code="A101", capacity=50)
            db.session.add(room_a101)

        room_b202 = Room.query.filter_by(code="B202").first()
        if room_b202 is None:
            room_b202 = Room(code="B202", capacity=50)
            db.session.add(room_b202)

        db.session.commit()

        # Course classes
        class_python = CourseClass.query.filter_by(class_code="ITEC1401-01").first()
        if class_python is None:
            class_python = CourseClass(
                course_id=course_python.id,
                semester_id=semester.id,
                class_code="ITEC1401-01",
                max_students=50,
                current_students=0,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_python)

        class_oop = CourseClass.query.filter_by(class_code="ITEC2504-01").first()
        if class_oop is None:
            class_oop = CourseClass(
                course_id=course_oop.id,
                semester_id=semester.id,
                class_code="ITEC2504-01",
                max_students=50,
                current_students=0,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_oop)

        class_web = CourseClass.query.filter_by(class_code="ITEC3401-01").first()
        if class_web is None:
            class_web = CourseClass(
                course_id=course_web.id,
                semester_id=semester.id,
                class_code="ITEC3401-01",
                max_students=50,
                current_students=0,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_web)

        class_full = CourseClass.query.filter_by(class_code="ITEC4501-FULL").first()
        if class_full is None:
            class_full = CourseClass(
                course_id=course_testing.id,
                semester_id=semester.id,
                class_code="ITEC4501-FULL",
                max_students=50,
                current_students=50,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_full)

        db.session.commit()

        # Schedules
        if ClassSchedule.query.filter_by(course_class_id=class_python.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_python.id,
                room_id=room_a101.id,
                day_of_week=2,
                start_period=1,
                end_period=3
            ))

        if ClassSchedule.query.filter_by(course_class_id=class_oop.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_oop.id,
                room_id=room_b202.id,
                day_of_week=3,
                start_period=1,
                end_period=3
            ))

        if ClassSchedule.query.filter_by(course_class_id=class_web.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_web.id,
                room_id=room_a101.id,
                day_of_week=2,
                start_period=2,
                end_period=4
            ))

        if ClassSchedule.query.filter_by(course_class_id=class_full.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_full.id,
                room_id=room_b202.id,
                day_of_week=4,
                start_period=1,
                end_period=3
            ))

        # Completed course: student01 đã học Nhập môn lập trình
        student = Student.query.filter_by(student_code="SV001").first()

        completed = CompletedCourse.query.filter_by(
            student_id=student.id,
            course_id=course_python.id
        ).first()

        if completed is None:
            completed = CompletedCourse(
                student_id=student.id,
                course_id=course_python.id,
                semester_id=semester.id,
                final_score=8.0,
                status=CompletedCourseStatus.PASSED
            )
            db.session.add(completed)

        db.session.commit()

        print("Seed data created successfully.")


if __name__ == "__main__":
    app.run(debug=True)