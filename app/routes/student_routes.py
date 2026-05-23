from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user

from app.models import UserRole, Student, Enrollment, EnrollmentStatus, CompletedCourse, Semester
from app.extensions import db
from datetime import date
from app.utils import role_required
from app.repositories.course_class_repository import get_all_classes
from app.services.enrollment_service import (
    register_course,
    calculate_credits_after_pending_cancel,
    can_confirm_registration,
    validate_registration_window,
    validate_cancel_draft,
    cancel_pending_enrollments,
    can_cancel_enrollment,
    MIN_CREDITS,
    MAX_CREDITS,
)

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_current_student():
    return Student.query.filter_by(user_id=current_user.id).first()


def _get_pending_cancel_ids():
    raw_ids = session.get("pending_cancel_ids", [])
    pending_ids = []

    for raw_id in raw_ids:
        try:
            enrollment_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        if enrollment_id not in pending_ids:
            pending_ids.append(enrollment_id)

    return pending_ids


def _set_pending_cancel_ids(pending_ids):
    unique_ids = []
    for raw_id in pending_ids:
        try:
            enrollment_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        if enrollment_id not in unique_ids:
            unique_ids.append(enrollment_id)

    session["pending_cancel_ids"] = unique_ids


@student_bp.route("/classes")
@login_required
@role_required(UserRole.STUDENT)
def class_list():
    student = get_current_student()

    classes = []
    active_semester = Semester.query.filter_by(is_active=True).first()
    semester = active_semester

    enrollments = []
    total_credits = 0
    can_confirm = False
    confirm_message = "Không tìm thấy thông tin sinh viên"
    class_list_notice = None
    pending_cancel_ids = _get_pending_cancel_ids()

    if student is not None:
        semester = active_semester

        if semester is not None:
            window_error = validate_registration_window(student, semester, date.today())
            if window_error is not None:
                class_list_notice = window_error
            else:
                classes = get_all_classes()
                classes = [c for c in classes if c.semester_id == semester.id]

            enrollments = Enrollment.query.filter_by(
                student_id=student.id,
                status=EnrollmentStatus.REGISTERED,
                semester_id=semester.id,
            ).all()

            total_credits = calculate_credits_after_pending_cancel(student.id, semester.id, pending_cancel_ids)
            can_confirm, confirm_message = can_confirm_registration(
                student.id,
                semester.id,
                total_credits=total_credits,
            )
        else:
            semester = None

    return render_template(
        "class_list.html",
        classes=classes,
        enrollments=enrollments,
        semester=semester,
        total_credits=total_credits,
        can_confirm=can_confirm,
        confirm_message=confirm_message,
        class_list_notice=class_list_notice,
        min_credits=MIN_CREDITS,
        max_credits=MAX_CREDITS,
        pending_cancel_ids=pending_cancel_ids,
    )


@student_bp.route("/completed")
@login_required
@role_required(UserRole.STUDENT)
def completed_courses():
    student = get_current_student()

    if student is None:
        flash("Không tìm thấy thông tin sinh viên", "danger")
        return redirect(url_for("auth.student_dashboard"))

    completed = CompletedCourse.query.filter_by(student_id=student.id).all()

    total_credits = 0
    if completed:
        try:
            total_credits = sum(c.course.credits or 0 for c in completed)
        except Exception:
            total_credits = 0

    return render_template(
        "completed_courses.html",
        completed_courses=completed,
        total_credits=total_credits
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


@student_bp.route("/enrollments/<int:enrollment_id>/cancel-draft", methods=["POST"])
@login_required
@role_required(UserRole.STUDENT)
def cancel_draft(enrollment_id):
    student = get_current_student()

    if student is None:
        flash("Không tìm thấy thông tin sinh viên", "danger")
        return redirect(url_for("student.class_list"))

    enrollment, error = validate_cancel_draft(student.id, enrollment_id)
    if error is not None:
        flash(error, "danger")
        return redirect(url_for("student.class_list"))

    ok, err = can_cancel_enrollment(student.id, enrollment.id)
    if not ok:
        flash(err, "danger")
        return redirect(url_for("student.class_list"))

    pending_cancel_ids = _get_pending_cancel_ids()
    if enrollment.id not in pending_cancel_ids:
        pending_cancel_ids.append(enrollment.id)
        _set_pending_cancel_ids(pending_cancel_ids)

    flash("Đã đưa học phần vào danh sách chờ hủy.", "success")
    return redirect(url_for("student.class_list"))


@student_bp.route("/enrollments/<int:enrollment_id>/cancel-draft/remove", methods=["POST"])
@login_required
@role_required(UserRole.STUDENT)
def remove_cancel_draft(enrollment_id):
    pending_cancel_ids = _get_pending_cancel_ids()
    try:
        enrollment_id = int(enrollment_id)
    except (TypeError, ValueError):
        enrollment_id = None

    if enrollment_id is not None and enrollment_id in pending_cancel_ids:
        pending_cancel_ids = [pending_id for pending_id in pending_cancel_ids if pending_id != enrollment_id]
        _set_pending_cancel_ids(pending_cancel_ids)

    flash("Đã bỏ học phần khỏi danh sách chờ hủy.", "success")
    return redirect(url_for("student.class_list"))


@student_bp.route("/enrollments/confirm", methods=["POST"])
@login_required
@role_required(UserRole.STUDENT)
def confirm_registration():
    student = get_current_student()

    if student is None:
        flash("Không tìm thấy thông tin sinh viên", "danger")
        return redirect(url_for("student.class_list"))

    pending_cancel_ids = _get_pending_cancel_ids()

    enrollments = Enrollment.query.filter_by(
        student_id=student.id,
        status=EnrollmentStatus.REGISTERED
    ).all()

    if not enrollments:
        flash("Bạn chưa đăng ký học phần nào", "danger")
        return redirect(url_for("student.class_list"))

    semester_id = enrollments[0].semester_id
    total_credits_after_cancel = calculate_credits_after_pending_cancel(
        student.id,
        semester_id,
        pending_cancel_ids,
    )

    can_confirm, message = can_confirm_registration(
        student.id,
        semester_id,
        total_credits=total_credits_after_cancel,
    )

    if not can_confirm:
        flash(message, "danger")
        return redirect(url_for("student.class_list"))

    _cancelled_ids, cancel_messages = cancel_pending_enrollments(
        student.id,
        pending_cancel_ids,
        current_date=date.today(),
    )

    for message_text in cancel_messages:
        flash(message_text, "danger")

    session.pop("pending_cancel_ids", None)

    flash("Xác nhận đăng ký học kỳ thành công", "success")
    return redirect(url_for("student.class_list"))