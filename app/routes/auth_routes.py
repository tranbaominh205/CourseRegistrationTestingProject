from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import UserRole, Student
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


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    # Support both GET and POST so tests and UI can use either method
    logout_user()
    # After logout, redirect to the login page
    return redirect(url_for("auth.login"))


@auth_bp.route('/api/auth/status')
def auth_status():
    # Return simple JSON indicating whether the current session is authenticated
    return jsonify({"authenticated": current_user.is_authenticated})


@auth_bp.route("/student/dashboard")
@login_required
@role_required(UserRole.STUDENT)
def student_dashboard():
    student = Student.query.filter_by(user_id=current_user.id).first()

    return render_template(
        "student_dashboard.html",
        student=student
    )


@auth_bp.route("/admin/dashboard")
@login_required
@role_required(UserRole.ADMIN)
def admin_dashboard():
    return render_template("admin_dashboard.html")