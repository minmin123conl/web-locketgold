#!/usr/bin/env python3
"""Database models và khởi tạo kết nối PostgreSQL."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from config import DATABASE_URL

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    balance = db.Column(db.Numeric(12, 0), default=0, nullable=False)  # số dư VNĐ
    credits = db.Column(db.Integer, default=0, nullable=False)  # số lượt
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    transactions = db.relationship("Transaction", backref="user", lazy=True)
    gold_orders = db.relationship("GoldOrder", backref="user", lazy=True)
    support_tickets = db.relationship("SupportTicket", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "balance": float(self.balance or 0),
            "credits": self.credits,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)  # topup | buy_credit | activate_gold
    amount = db.Column(db.Numeric(12, 0), default=0, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending | success | failed | cancelled
    order_code = db.Column(db.String(64), unique=True, nullable=True, index=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "amount": float(self.amount or 0),
            "status": self.status,
            "order_code": self.order_code,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GoldOrder(db.Model):
    __tablename__ = "gold_orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    uid = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending | success | failed
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "uid": self.uid,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SupportTicket(db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="open", nullable=False)  # open | in_progress | resolved | closed
    admin_reply = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "subject": self.subject,
            "message": self.message,
            "status": self.status,
            "admin_reply": self.admin_reply,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def _migrate_schema():
    """Thêm các cột mới vào bảng đã tồn tại nếu thiếu.

    Các câu ALTER TABLE phải tương thích cả SQLite lẫn PostgreSQL:
    - Kiểu thời gian: SQLite dùng DATETIME, PostgreSQL phải dùng TIMESTAMP
      (nếu không, Postgres báo lỗi 'type "datetime" does not exist').
    - Mặc định boolean: SQLite dùng 0/1, PostgreSQL cần TRUE/FALSE.
    """
    from sqlalchemy import inspect, text

    dialect = db.engine.dialect.name
    is_postgres = dialect in ("postgresql", "postgres")
    ts_type = "TIMESTAMP" if is_postgres else "DATETIME"
    false_default = "FALSE" if is_postgres else "0"
    true_default = "TRUE" if is_postgres else "1"

    inspector = inspect(db.engine)
    existing_columns = {col["name"] for col in inspector.get_columns("users")}

    # Thêm cột is_admin nếu thiếu
    if "is_admin" not in existing_columns:
        db.session.execute(text(f"ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT {false_default} NOT NULL"))
        db.session.commit()

    # Thêm cột credits nếu thiếu
    if "credits" not in existing_columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 0 NOT NULL"))
        db.session.commit()

    # Thêm cột balance nếu thiếu
    if "balance" not in existing_columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN balance NUMERIC(12,0) DEFAULT 0 NOT NULL"))
        db.session.commit()

    # Thêm cột is_active nếu thiếu
    if "is_active" not in existing_columns:
        db.session.execute(text(f"ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT {true_default} NOT NULL"))
        db.session.commit()

    # Thêm cột last_login nếu thiếu
    if "last_login" not in existing_columns:
        db.session.execute(text(f"ALTER TABLE users ADD COLUMN last_login {ts_type}"))
        db.session.commit()

    # Kiểm tra bảng transactions
    if inspector.has_table("transactions"):
        tx_columns = {col["name"] for col in inspector.get_columns("transactions")}
        if "order_code" not in tx_columns:
            db.session.execute(text("ALTER TABLE transactions ADD COLUMN order_code VARCHAR(64)"))
            db.session.commit()
        if "description" not in tx_columns:
            db.session.execute(text("ALTER TABLE transactions ADD COLUMN description VARCHAR(255)"))
            db.session.commit()
        if "updated_at" not in tx_columns:
            db.session.execute(text(f"ALTER TABLE transactions ADD COLUMN updated_at {ts_type}"))
            db.session.commit()

    # Kiểm tra bảng support_tickets
    if inspector.has_table("support_tickets"):
        st_columns = {col["name"] for col in inspector.get_columns("support_tickets")}
        if "admin_reply" not in st_columns:
            db.session.execute(text("ALTER TABLE support_tickets ADD COLUMN admin_reply TEXT"))
            db.session.commit()
        if "updated_at" not in st_columns:
            db.session.execute(text(f"ALTER TABLE support_tickets ADD COLUMN updated_at {ts_type}"))
            db.session.commit()


def init_db_app(app):
    """Gắn SQLAlchemy vào Flask app (SETUP thuần, không network I/O).

    An toàn để gọi ở cấp module / lúc import: Vercel import entrypoint
    trong lúc BUILD để tìm WSGI app. Nếu gọi network I/O ở đây (ví dụ
    create_all), build sẽ crash -> FUNCTION_INVOCATION_FAILED.
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)


def init_db_data(app):
    """Tạo bảng, migrate schema và tạo admin mặc định (network I/O).

    Chỉ gọi khi thực sự cần (request đầu tiên), không gọi lúc import.
    Lỗi DB sẽ được route /healthz báo cáo cụ thể.

    Nhận `app` trực tiếp (không dựa vào `db.app` — vài bản Flask-SQLAlchemy
    không set `db.app` khi dùng cú pháp init_app).
    """
    with app.app_context():
        db.create_all()
        # Migration schema cho database cũ
        _migrate_schema()
        # Tạo admin user mặc định nếu chưa có
        from config import ADMIN_USERNAME, ADMIN_PASSWORD
        admin = User.query.filter_by(username=ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=ADMIN_USERNAME,
                email=f"{ADMIN_USERNAME}@admin.local",
                is_admin=True,
                is_active=True,
            )
            admin.set_password(ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()


# Backward-compat: giữ hàm cũ cho code/test khác vẫn gọi init_db(app)
def init_db(app):
    init_db_app(app)
    init_db_data(app)
