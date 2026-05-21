from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import UserRole
from app.services.admin_service import (
    AdminServiceError,
    create_course_class,
    delete_course_class,
    get_admin_form_options,
    get_all_course_classes,
    get_course_class_or_404,
    update_course_class,
)
from app.utils import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/classes")
@login_required
@role_required(UserRole.ADMIN)
def class_list():
    classes = get_all_course_classes()
    return render_template("admin_dashboard.html", classes=classes)


@admin_bp.route("/classes/create", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def create_class():
    options = get_admin_form_options()

    if request.method == "GET":
        return render_template(
            "admin_class_form.html",
            title="Tạo lớp học phần",
            options=options,
            course_class=None,
            schedule=None,
        )

    try:
        create_course_class(request.form)
        flash("Tạo lớp học phần thành công", "success")
        return redirect(url_for("admin.class_list"))
    except AdminServiceError as error:
        flash(str(error), "error")
        return render_template(
            "admin_class_form.html",
            title="Tạo lớp học phần",
            options=options,
            course_class=None,
            schedule=None,
        ), 400


@admin_bp.route("/classes/<int:course_class_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def edit_class(course_class_id):
    course_class = get_course_class_or_404(course_class_id)

    if course_class is None:
        flash("Không tìm thấy lớp học phần", "error")
        return redirect(url_for("admin.class_list"))

    schedule = course_class.schedules[0] if course_class.schedules else None
    options = get_admin_form_options()

    if request.method == "GET":
        return render_template(
            "admin_class_form.html",
            title="Cập nhật lớp học phần",
            options=options,
            course_class=course_class,
            schedule=schedule,
        )

    try:
        update_course_class(course_class_id, request.form)
        flash("Cập nhật lớp học phần thành công", "success")
        return redirect(url_for("admin.class_list"))
    except AdminServiceError as error:
        flash(str(error), "error")
        return render_template(
            "admin_class_form.html",
            title="Cập nhật lớp học phần",
            options=options,
            course_class=course_class,
            schedule=schedule,
        ), 400


@admin_bp.route("/classes/<int:course_class_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def delete_class(course_class_id):
    try:
        delete_course_class(course_class_id)
        flash("Xoá lớp học phần thành công", "success")
    except AdminServiceError as error:
        flash(str(error), "error")

    return redirect(url_for("admin.class_list"))