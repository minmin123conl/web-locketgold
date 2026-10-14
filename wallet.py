#!/usr/bin/env python3
"""Xử lý số dư, mua lượt, trừ/hoàn credit."""
import uuid

from config import CREDIT_PRICE
from database import Transaction, User, db


def create_topup_transaction(user_id, amount):
    """Tạo transaction nạp tiền (pending)."""
    # PayOS yêu cầu orderCode là số nguyên dương, tối đa 10 chữ số
    import random
    order_code = str(random.randint(1000000000, 9999999999))
    # Đảm bảo unique trong database
    while Transaction.query.filter_by(order_code=order_code).first():
        order_code = str(random.randint(1000000000, 9999999999))
    tx = Transaction(
        user_id=user_id,
        type="topup",
        amount=amount,
        status="pending",
        order_code=order_code,
        description=f"Nạp tiền {amount}đ",
    )
    db.session.add(tx)
    db.session.commit()
    return tx


def mark_topup_success(order_code):
    """Đánh dấu transaction nạp tiền thành công (idempotent)."""
    tx = Transaction.query.filter_by(order_code=order_code, type="topup").first()
    if not tx:
        return None, "Không tìm thấy giao dịch."
    if tx.status == "success":
        return tx, None  # đã xử lý rồi, không cộng trùng

    user = db.session.get(User, tx.user_id)
    if not user:
        return None, "Không tìm thấy user."

    tx.status = "success"
    user.balance = (user.balance or 0) + tx.amount
    db.session.commit()
    return tx, None


def buy_credit(user):
    """Mua 1 lượt, trừ balance."""
    if (user.balance or 0) < CREDIT_PRICE:
        return None, f"Số dư không đủ. Cần {CREDIT_PRICE}đ."

    user.balance = (user.balance or 0) - CREDIT_PRICE
    user.credits = (user.credits or 0) + 1

    tx = Transaction(
        user_id=user.id,
        type="buy_credit",
        amount=CREDIT_PRICE,
        status="success",
        description="Mua 1 lượt kích hoạt Gold",
    )
    db.session.add(tx)
    db.session.commit()
    return tx, None


def use_credit(user):
    """Trừ 1 credit khi kích hoạt Gold."""
    if (user.credits or 0) < 1:
        return None, "Bạn không có lượt nào. Hãy mua lượt trước."

    user.credits = (user.credits or 0) - 1
    db.session.commit()
    return True, None


def refund_credit(user):
    """Hoàn lại 1 credit khi kích hoạt thất bại."""
    user.credits = (user.credits or 0) + 1
    db.session.commit()


def get_transactions(user_id, limit=50):
    """Lấy lịch sử giao dịch."""
    return (
        Transaction.query
        .filter_by(user_id=user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )