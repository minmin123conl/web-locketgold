#!/usr/bin/env python3
"""Bảo mật: Rate limiting, CSRF protection, Security headers."""
import hashlib
import hmac
import time
from collections import defaultdict
from functools import wraps

from flask import jsonify, request, session

import config

# ════════════════════════════════════════════════════════════════════
# RATE LIMITING (in-memory, đủ cho single instance)
# ════════════════════════════════════════════════════════════════════
_rate_store = defaultdict(list)  # key -> list of timestamps


def _get_client_ip():
    """Lấy IP thật của client (hỗ trợ proxy)."""
    # Nếu chạy sau proxy (nginx, cloudflare...)
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    return request.remote_addr or "unknown"


def _rate_key(scope, identifier=None):
    """Tạo key cho rate limit."""
    ip = _get_client_ip()
    if identifier:
        return f"{scope}:{identifier}:{ip}"
    return f"{scope}:{ip}"


def _check_rate_limit(scope, limit, window_seconds, identifier=None):
    """Kiểm tra rate limit. Trả True nếu vượt giới hạn."""
    if not config.RATE_LIMIT_ENABLED:
        return False

    key = _rate_key(scope, identifier)
    now = time.time()
    # Xóa các timestamp cũ hơn window
    _rate_store[key] = [t for t in _rate_store[key] if now - t < window_seconds]

    if len(_rate_store[key]) >= limit:
        return True

    _rate_store[key].append(now)
    return False


def rate_limit(scope, limit=None, window_seconds=60, identifier=None):
    """Decorator rate limit cho route."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            actual_limit = limit or config.RATE_LIMIT_DEFAULT
            if _check_rate_limit(scope, actual_limit, window_seconds, identifier):
                return jsonify({
                    "ok": False,
                    "error": "Bạn thao tác quá nhanh. Vui lòng thử lại sau."
                }), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ════════════════════════════════════════════════════════════════════
# CSRF PROTECTION
# ════════════════════════════════════════════════════════════════════
def generate_csrf_token():
    """Tạo CSRF token cho session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = hmac.new(
            config.SECRET_KEY.encode("utf-8"),
            str(time.time()).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    return session["_csrf_token"]


def validate_csrf_token(token):
    """Kiểm tra CSRF token."""
    if not config.CSRF_ENABLED:
        return True
    expected = session.get("_csrf_token")
    if not expected or not token:
        return False
    return hmac.compare_digest(expected, token)


def csrf_protect(f):
    """Decorator bảo vệ CSRF cho POST/PUT/DELETE requests."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # Lấy token từ header hoặc form
            token = request.headers.get("X-CSRF-Token") or request.form.get("_csrf_token")
            if not validate_csrf_token(token):
                # Nếu là API request -> trả JSON
                if request.path.startswith("/api/"):
                    return jsonify({"ok": False, "error": "CSRF token không hợp lệ."}), 403
                return "CSRF token không hợp lệ.", 403
        return f(*args, **kwargs)
    return wrapped


# ════════════════════════════════════════════════════════════════════
# SECURITY HEADERS
# ════════════════════════════════════════════════════════════════════
def add_security_headers(response):
    """Thêm các security headers vào response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    return response


# ════════════════════════════════════════════════════════════════════
# INPUT VALIDATION HELPERS
# ════════════════════════════════════════════════════════════════════
def validate_username(username):
    """Kiểm tra username hợp lệ."""
    if not username or len(username) < 3 or len(username) > 50:
        return False, "Tên đăng nhập phải từ 3-50 ký tự."
    if not all(c.isalnum() or c in "._-" for c in username):
        return False, "Tên đăng nhập chỉ chứa chữ, số, dấu chấm, gạch dưới, gạch ngang."
    return True, None


def validate_email(email):
    """Kiểm tra email hợp lệ."""
    if not email or len(email) > 120:
        return False, "Email không hợp lệ."
    if "@" not in email or "." not in email.split("@")[-1]:
        return False, "Email không hợp lệ."
    return True, None


def validate_password(password):
    """Kiểm tra mật khẩu mạnh."""
    if not password or len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự."
    if len(password) > 128:
        return False, "Mật khẩu quá dài."
    return True, None


def validate_uid(uid):
    """Kiểm tra UID Locket hợp lệ (28 ký tự alphanumeric)."""
    if not uid or len(uid) != 28:
        return False, "UID Locket phải có 28 ký tự."
    if not all(c.isalnum() for c in uid):
        return False, "UID Locket chỉ chứa chữ và số."
    return True, None


def validate_amount(amount):
    """Kiểm tra số tiền nạp hợp lệ."""
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return None, "Số tiền không hợp lệ."
    if amount < 1000:
        return None, "Số tiền nạp tối thiểu 1.000đ."
    if amount > 100000000:  # 100 triệu
        return None, "Số tiền nạp tối đa 100.000.000đ."
    return amount, None