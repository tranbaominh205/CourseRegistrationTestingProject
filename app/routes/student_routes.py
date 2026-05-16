from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import UserRole, Student, Enrollment, EnrollmentStatus
from app.utils import role_required
from app.repositories.course_class_repository import get_all_classes
from app.services.enrollment_service import register_course

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_current_student():
    return Student.query.filter_by(user_id=current_user.id).first()


@student_bp.route("/classes")
@login_required
@role_required(UserRole.STUDENT)
def class_list():
    classes = get_all_classes()
    return render_template("class_list.html", classes=classes)


@student_bp.route("/classes/<int:course_class_id>/register", methods=["POST"])
@login_required
@role_required(UserRole.STUDENT)
def register_class(course_class_id):
    student = get_current_student()

    if student is None:
        flash("Student profile not found", "danger")
        return redirect(url_for("student.class_list"))

    enrollment, error = register_course(student.id, course_class_id)

    if error:
        flash(error, "danger")
        return redirect(url_for("student.class_list"))

    flash("Register course successfully", "success")
    return redirect(url_for("student.my_enrollments"))


@student_bp.route("/my-enrollments")
@login_required
@role_required(UserRole.STUDENT)
def my_enrollments():
    student = get_current_student()

    enrollments = Enrollment.query.filter_by(
        student_id=student.id,
        status=EnrollmentStatus.REGISTERED
    ).all()

    return render_template("my_enrollments.html", enrollments=enrollments)