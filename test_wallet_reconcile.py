#!/usr/bin/env python3
"""Test hồi quy: nạp tiền phải được cộng khi quay về /vi từ payOS.

Chạy: python3 test_wallet_reconcile.py
Dùng SQLite tạm + mock payos.get_payment_status (không gọi mạng).
"""
import os
import sys
import tempfile

DB_FILE = os.path.join(tempfile.mkdtemp(), "test_reconcile.db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE}"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["CSRF_ENABLED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["SESSION_COOKIE_SECURE"] = "false"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as app_module  # noqa: E402
import payos  # noqa: E402
from database import db, User, Transaction  # noqa: E402
from wallet import create_topup_transaction  # noqa: E402

failures = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        failures.append(name)


def mock_paid(order_code):
    return {"status": "PAID", "orderCode": int(order_code)}, None


def mock_pending(order_code):
    return {"status": "PENDING", "orderCode": int(order_code)}, None


def new_user(username):
    with app_module.app.app_context():
        u = User(username=username, email=f"{username}@t.local")
        u.set_password("x")
        db.session.add(u)
        db.session.commit()
        return u.id


def make_tx(user_id, amount):
    with app_module.app.app_context():
        tx = create_topup_transaction(user_id, amount)
        return tx.order_code


def balance_of(user_id):
    with app_module.app.app_context():
        return float(db.session.get(User, user_id).balance or 0)


def tx_status(order_code):
    with app_module.app.app_context():
        tx = Transaction.query.filter_by(order_code=str(order_code)).first()
        return tx.status if tx else None


def main():
    app_module.app.config["TESTING"] = True
    with app_module.app.app_context():
        app_module.init_db_data(app_module.app)

    client = app_module.app.test_client()

    # ── Case 1: /vi?orderCode=<code> (camelCase), đơn PAID ───────────
    uid = new_user("u1")
    code = make_tx(uid, 50000)
    payos.get_payment_status = mock_paid
    with client.session_transaction() as sess:
        sess["user_id"] = uid
    r = client.get(f"/vi?orderCode={code}", follow_redirects=True)
    check("case1 http 200", r.status_code == 200, r.status_code)
    check("case1 balance +50000", balance_of(uid) == 50000, balance_of(uid))
    check("case1 tx success", tx_status(code) == "success", tx_status(code))

    # ── Case 2: refresh, không cộng trùng ────────────────────────────
    r = client.get(f"/vi?status=success&order_code={code}", follow_redirects=True)
    check("case2 http 200", r.status_code == 200, r.status_code)
    check("case2 không cộng trùng", balance_of(uid) == 50000, balance_of(uid))

    # ── Case 3: đơn chưa PAID -> không cộng ──────────────────────────
    uid3 = new_user("u3")
    code3 = make_tx(uid3, 20000)
    payos.get_payment_status = mock_pending
    with client.session_transaction() as sess:
        sess["user_id"] = uid3
    r = client.get(f"/vi?order_code={code3}", follow_redirects=True)
    check("case3 http 200", r.status_code == 200, r.status_code)
    check("case3 không cộng khi chưa PAID", balance_of(uid3) == 0, balance_of(uid3))

    # ── Case 4: /api/wallet/sync nhận camelCase ──────────────────────
    payos.get_payment_status = mock_paid
    uid4 = new_user("u4")
    code4 = make_tx(uid4, 10000)
    with client.session_transaction() as sess:
        sess["user_id"] = uid4
    r = client.post("/api/wallet/sync", json={"orderCode": code4})
    check("case4 http 200", r.status_code == 200, r.status_code)
    check("case4 ok+success", r.get_json().get("status") == "success", r.get_json())
    check("case4 balance +10000", balance_of(uid4) == 10000, balance_of(uid4))

    # ── Case 5: đơn của user khác -> 404, không cộng ─────────────────
    uid5 = new_user("u5")
    with client.session_transaction() as sess:
        sess["user_id"] = uid5
    r = client.post("/api/wallet/sync", json={"order_code": code4})
    check("case5 http 404", r.status_code == 404, r.status_code)
    check("case5 không cộng", balance_of(uid5) == 0, balance_of(uid5))

    print()
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())