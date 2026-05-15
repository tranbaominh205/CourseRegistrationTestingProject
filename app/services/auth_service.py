from werkzeug.security import check_password_hash
from app.repositories.user_repository import get_user_by_username


def authenticate_user(username, password):
    if not username or not password:
        return None, "Username and password are required"

    user = get_user_by_username(username.strip())

    if user is None:
        return None, "Tài khoản không tồn tại"

    if not user.is_active:
        return None, "Account is inactive"

    if not check_password_hash(user.password_hash, password):
        return None, "Sai mật khẩu"

    return user, None