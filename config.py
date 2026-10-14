#!/usr/bin/env python3
"""Cấu hình cho web-locketgold."""
import os

# ════════════════════════════════════════════════════════════════════
# DATABASE (PostgreSQL hoặc SQLite cho local test)
# ════════════════════════════════════════════════════════════════════
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///locketgold.db"  # fallback SQLite nếu không có PostgreSQL
)

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