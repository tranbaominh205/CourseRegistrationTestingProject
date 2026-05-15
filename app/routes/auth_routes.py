from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required

from app.models import UserRole
from app.services.auth_service import authenticate_user
from app.utils import role_required

auth_bp = Blueprint("auth", __name__)


INVALID_CREDENTIAL_ERRORS = {
    "Tài khoản không tồn tại",
    "Sai mật khẩu",
}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    user, error = authenticate_user(username, password)

    if error:
        message = "Invalid username or password" if error in INVALID_CREDENTIAL_ERRORS else error
        flash(message, "error")
        return render_template("login.html"), 401

    login_user(user)

    if user.role == UserRole.ADMIN:
        return redirect(url_for("auth.admin_dashboard"))

    return redirect(url_for("auth.student_dashboard"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/student/dashboard")
@login_required
@role_required(UserRole.STUDENT)
def student_dashboard():
    return render_template("student_dashboard.html")


@auth_bp.route("/admin/dashboard")
@login_required
@role_required(UserRole.ADMIN)
def admin_dashboard():
    return render_template("admin_dashboard.html")