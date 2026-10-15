#!/usr/bin/env python3
"""Xử lý đăng ký, đăng nhập, đăng xuất."""
from datetime import datetime, timezone
from functools import wraps

from flask import jsonify, redirect, request, session, url_for

from database import User, db
from security import validate_email, validate_password, validate_username


def login_required(f):
    """Decorator yêu cầu đăng nhập."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # Nếu là API request -> trả JSON
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "error": "Vui lòng đăng nhập."}), 401
            # Nếu là trang web -> redirect về đăng nhập
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator yêu cầu quyền admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "error": "Vui lòng đăng nhập."}), 401
            return redirect(url_for("login", next=request.path))

        user = db.session.get(User, session["user_id"])
        if not user or not user.is_admin:
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "error": "Bạn không có quyền truy cập."}), 403
            return "Bạn không có quyền truy cập.", 403

        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Lấy user hiện tại từ session."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def register_user(username, email, password):
    """Đăng ký user mới."""
    # Validate input
    ok, error = validate_username(username)
    if not ok:
        return None, error
    ok, error = validate_email(email)
    if not ok:
        return None, error
    ok, error = validate_password(password)
    if not ok:
        return None, error

    # Kiểm tra trùng
    if User.query.filter_by(username=username).first():
        return None, "Tên đăng nhập đã tồn tại."
    if User.query.filter_by(email=email).first():
        return None, "Email đã tồn tại."

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user, None


def login_user(username, password):
    """Đăng nhập."""
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return None, "Tên đăng nhập hoặc mật khẩu không đúng."

    if not user.is_active:
        return None, "Tài khoản đã bị khóa. Liên hệ hỗ trợ."

    # Cập nhật last_login
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    return user, None