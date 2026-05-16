from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import UserRole, Student, Enrollment, EnrollmentStatus
from app.utils import role_required
from app.repositories.course_class_repository import get_all_classes
from app.services.enrollment_service import (
    register_course,
    calculate_registered_credits,
    can_confirm_registration,
)

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_current_student():
    return Student.query.filter_by(user_id=current_user.id).first()


@student_bp.route("/classes")
@login_required
@role_required(UserRole.STUDENT)
def class_list():
    student = get_current_student()

    classes = get_all_classes()
    enrollments = []
    total_credits = 0
    can_confirm = False
    confirm_message = "Không tìm thấy thông tin sinh viên"

    if student is not None:
        enrollments = Enrollment.query.filter_by(
            student_id=student.id,
            status=EnrollmentStatus.REGISTERED
        ).all()

        if enrollments:
            semester_id = enrollments[0].semester_id
        elif classes:
            semester_id = classes[0].semester_id
        else:
            semester_id = None

        if semester_id is not None:
            total_credits = calculate_registered_credits(student.id, semester_id)
            can_confirm, confirm_message = can_confirm_registration(student.id, semester_id)

    return render_template(
        "class_list.html",
        classes=classes,
        enrollments=enrollments,
        total_credits=total_credits,
        can_confirm=can_confirm,
        confirm_message=confirm_message
    )


@student_bp.route("/classes/<int:course_class_id>/register", methods=["POST"])
@login_required
@role_required(UserRole.STUDENT)
def register_class(course_class_id):
    student = get_current_student()

    if student is None:
        flash("Không tìm thấy thông tin sinh viên", "danger")
        return redirect(url_for("student.class_list"))

    enrollment, error = register_course(student.id, course_class_id)

    if error:
        flash(error, "danger")
        return redirect(url_for("student.class_list"))

    flash("Đăng ký học phần thành công", "success")
    return redirect(url_for("student.class_list"))


@student_bp.route("/enrollments/confirm", methods=["POST"])
@login_required
@role_required(UserRole.STUDENT)
def confirm_registration():
    student = get_current_student()

    if student is None:
        flash("Không tìm thấy thông tin sinh viên", "danger")
        return redirect(url_for("student.class_list"))

    enrollments = Enrollment.query.filter_by(
        student_id=student.id,
        status=EnrollmentStatus.REGISTERED
    ).all()

    if not enrollments:
        flash("Bạn chưa đăng ký học phần nào", "danger")
        return redirect(url_for("student.class_list"))

    semester_id = enrollments[0].semester_id
    can_confirm, message = can_confirm_registration(student.id, semester_id)

    if not can_confirm:
        flash(message, "danger")
        return redirect(url_for("student.class_list"))

    flash("Xác nhận đăng ký học kỳ thành công", "success")
    return redirect(url_for("student.class_list"))