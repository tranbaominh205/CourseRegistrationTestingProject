from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, login_manager


class UserRole:
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.STUDENT)
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active(self):
        return self.is_active_account


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    student_code = db.Column(db.String(20), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=False)

    user = db.relationship("User", backref="student_profile")


class Semester(db.Model):
    __tablename__ = "semesters"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    registration_start_date = db.Column(db.Date, nullable=False)
    registration_end_date = db.Column(db.Date, nullable=False)
    cancel_deadline = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False)


class CourseClass(db.Model):
    __tablename__ = "course_classes"

    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String(30), nullable=False, unique=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)
    max_students = db.Column(db.Integer, nullable=False, default=50)
    current_students = db.Column(db.Integer, nullable=False, default=0)

    course = db.relationship("Course")
    semester = db.relationship("Semester")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))