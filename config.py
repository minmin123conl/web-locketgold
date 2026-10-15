#!/usr/bin/env python3
"""Cấu hình cho web-locketgold."""
import os

# ════════════════════════════════════════════════════════════════════
# MÔI TRƯỜNG CHẠY
# ════════════════════════════════════════════════════════════════════
# Vercel cung cấp biến môi trường VERCEL=1 khi chạy serverless.
# Trên Vercel filesystem là READ-ONLY, chỉ /tmp là ghi được.
IS_VERCEL = bool(os.environ.get("VERCEL"))

# Thư mục instance (Flask dùng để lưu file tạm, SQLite mặc định).
# Trên Vercel bắt buộc phải nằm trong /tmp, nếu không sẽ lỗi
# "OSError: [Errno 30] Read-only file system: '/var/task/instance'".
INSTANCE_PATH = os.environ.get(
    "INSTANCE_PATH",
    "/tmp/instance" if IS_VERCEL else "instance",
)

# ════════════════════════════════════════════════════════════════════
# DATABASE (PostgreSQL hoặc SQLite cho local test)
# ════════════════════════════════════════════════════════════════════
# LƯU Ý: nên đặt biến môi trường DATABASE_URL (PostgreSQL) trên Vercel
# để dữ liệu được lưu vĩnh viễn. SQLite chỉ là fallback (trên Vercel
# dữ liệu sẽ mất sau mỗi lần cold start vì /tmp là tạm thời).
def _normalize_db_url(url):
    """Chuẩn hoá DATABASE_URL để tương thích với psycopg2/libpq.

    - Bỏ khoảng trắng và cặp nháy bao ngoài (lỗi thường gặp khi dán vào
      Environment Variables trên Vercel:  DATABASE_URL="postgres://...").
    - Đổi scheme 'postgres://' -> 'postgresql://' (SQLAlchemy yêu cầu).
    - Loại bỏ tham số '?channel_binding=require' mà Neon tự thêm: libpq
      đi kèm psycopg2-binary trên Vercel có thể không hỗ trợ tham số này,
      gây lỗi 'invalid connection option "channel_binding"' làm function
      crash lúc khởi động (FUNCTION_INVOCATION_FAILED).
    """
    if not url:
        return url

    url = url.strip()
    # Bỏ nháy đơn/nháy kép bao quanh nếu người dùng vô tình dán vào
    if len(url) >= 2 and url[0] == url[-1] and url[0] in ("'", '"'):
        url = url[1:-1].strip()

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    if "channel_binding" in url:
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        parts = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                 if k != "channel_binding"]
        url = urlunsplit((parts.scheme, parts.netloc, parts.path,
                          urlencode(query), parts.fragment))

    return url


DATABASE_URL = _normalize_db_url(os.environ.get(
    "DATABASE_URL",
    # 4 dấu / = đường dẫn tuyệt đối (/tmp/...); 3 dấu / = tương đối
    "sqlite:////tmp/locketgold.db" if IS_VERCEL else "sqlite:///locketgold.db",
))

# ════════════════════════════════════════════════════════════════════
# PAYOS (để trống, user sẽ bổ sung API key sau)
# ════════════════════════════════════════════════════════════════════
PAYOS_CLIENT_ID = os.environ.get("PAYOS_CLIENT_ID", "")
PAYOS_API_KEY = os.environ.get("PAYOS_API_KEY", "")
PAYOS_CHECKSUM_KEY = os.environ.get("PAYOS_CHECKSUM_KEY", "")
PAYOS_API_URL = os.environ.get("PAYOS_API_URL", "https://api-merchant.payos.vn")

# ════════════════════════════════════════════════════════════════════
# APP CONFIG
# ════════════════════════════════════════════════════════════════════
SECRET_KEY = os.environ.get("SECRET_KEY", "locket-gold-secret-key-change-me")
CREDIT_PRICE = int(os.environ.get("CREDIT_PRICE", "10000"))  # 10.000đ / lượt

# ════════════════════════════════════════════════════════════════════
# ADMIN CONFIG
# ════════════════════════════════════════════════════════════════════
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # ĐỔI MẬT KHẨU NÀY KHI TRIỂN KHAI!

# ════════════════════════════════════════════════════════════════════
# SECURITY CONFIG
# ════════════════════════════════════════════════════════════════════
# Rate limiting
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_DEFAULT = int(os.environ.get("RATE_LIMIT_DEFAULT", "60"))  # requests per minute
RATE_LIMIT_LOGIN = int(os.environ.get("RATE_LIMIT_LOGIN", "5"))  # login attempts per 15 min
RATE_LIMIT_REGISTER = int(os.environ.get("RATE_LIMIT_REGISTER", "3"))  # registrations per hour
RATE_LIMIT_INJECT = int(os.environ.get("RATE_LIMIT_INJECT", "10"))  # inject attempts per hour
RATE_LIMIT_RESOLVE = int(os.environ.get("RATE_LIMIT_RESOLVE", "30"))  # resolve attempts per hour
RATE_LIMIT_TOPUP = int(os.environ.get("RATE_LIMIT_TOPUP", "10"))  # topup attempts per hour

# Session cookie
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
PERMANENT_SESSION_LIFETIME = int(os.environ.get("PERMANENT_SESSION_LIFETIME", "86400"))  # 24h

# CSRF
CSRF_ENABLED = os.environ.get("CSRF_ENABLED", "true").lower() == "true"