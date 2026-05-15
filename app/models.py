from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, login_manager
from datetime import datetime, UTC


class UserRole:
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class EnrollmentStatus:
    REGISTERED = "REGISTERED"
    CANCELLED = "CANCELLED"


class CourseClassStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class CompletedCourseStatus:
    PASSED = "PASSED"
    FAILED = "FAILED"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default=UserRole.STUDENT)
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    student = db.relationship("Student", back_populates="user", uselist=False)

    @property
    def is_active(self):
        return self.is_active_account


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    student_code = db.Column(db.String(20), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    major = db.Column(db.String(100), nullable=True)

    user = db.relationship("User", back_populates="student")
    enrollments = db.relationship("Enrollment", back_populates="student")
    completed_courses = db.relationship("CompletedCourse", back_populates="student")


class Semester(db.Model):
    __tablename__ = "semesters"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)

    registration_start_date = db.Column(db.Date, nullable=False)
    registration_end_date = db.Column(db.Date, nullable=False)
    cancel_deadline = db.Column(db.Date, nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    course_classes = db.relationship("CourseClass", back_populates="semester")
    enrollments = db.relationship("Enrollment", back_populates="semester")


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)

    course_classes = db.relationship("CourseClass", back_populates="course")


class CoursePrerequisite(db.Model):
    __tablename__ = "course_prerequisites"

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    prerequisite_course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    course = db.relationship("Course", foreign_keys=[course_id])
    prerequisite_course = db.relationship("Course", foreign_keys=[prerequisite_course_id])

    __table_args__ = (
        db.UniqueConstraint(
            "course_id",
            "prerequisite_course_id",
            name="uq_course_prerequisite"
        ),
    )


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(20), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False)

    schedules = db.relationship("ClassSchedule", back_populates="room")


class CourseClass(db.Model):
    __tablename__ = "course_classes"

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)

    class_code = db.Column(db.String(30), nullable=False, unique=True)

    max_students = db.Column(db.Integer, nullable=False, default=50)
    current_students = db.Column(db.Integer, nullable=False, default=0)

    status = db.Column(db.String(20), nullable=False, default=CourseClassStatus.OPEN)

    course = db.relationship("Course", back_populates="course_classes")
    semester = db.relationship("Semester", back_populates="course_classes")
    schedules = db.relationship("ClassSchedule", back_populates="course_class")
    enrollments = db.relationship("Enrollment", back_populates="course_class")


class ClassSchedule(db.Model):
    __tablename__ = "class_schedules"

    id = db.Column(db.Integer, primary_key=True)

    course_class_id = db.Column(db.Integer, db.ForeignKey("course_classes.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)

    day_of_week = db.Column(db.Integer, nullable=False)
    start_period = db.Column(db.Integer, nullable=False)
    end_period = db.Column(db.Integer, nullable=False)

    course_class = db.relationship("CourseClass", back_populates="schedules")
    room = db.relationship("Room", back_populates="schedules")


class CompletedCourse(db.Model):
    __tablename__ = "completed_courses"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)

    final_score = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=CompletedCourseStatus.PASSED)

    student = db.relationship("Student", back_populates="completed_courses")
    course = db.relationship("Course")
    semester = db.relationship("Semester")

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_student_completed_course"
        ),
    )


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_class_id = db.Column(db.Integer, db.ForeignKey("course_classes.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)

    status = db.Column(db.String(20), nullable=False, default=EnrollmentStatus.REGISTERED)

    registered_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
    cancelled_at = db.Column(db.DateTime, nullable=True)

    midterm_exam_done = db.Column(db.Boolean, nullable=False, default=False)

    student = db.relationship("Student", back_populates="enrollments")
    course_class = db.relationship("CourseClass", back_populates="enrollments")
    semester = db.relationship("Semester", back_populates="enrollments")

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "course_class_id",
            name="uq_student_course_class"
        ),
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))