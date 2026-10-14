#!/usr/bin/env python3
"""Tích hợp payOS: tạo payment link + verify webhook."""
import hashlib
import hmac
import json
import logging
import urllib.parse

import requests

from config import (
    PAYOS_API_KEY,
    PAYOS_API_URL,
    PAYOS_CHECKSUM_KEY,
    PAYOS_CLIENT_ID,
)

logger = logging.getLogger(__name__)


def _signature(data: dict) -> str:
    """Tạo signature theo chuẩn payOS: HMAC-SHA256 của chuỗi query string."""
    # Sắp xếp key theo alphabet, bỏ key rỗng
    sorted_data = {k: str(v) for k, v in sorted(data.items()) if v not in (None, "")}
    query_string = urllib.parse.urlencode(sorted_data)
    return hmac.new(
        PAYOS_CHECKSUM_KEY.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def is_configured() -> bool:
    """Kiểm tra đã cấu hình payOS chưa."""
    return bool(PAYOS_CLIENT_ID and PAYOS_API_KEY and PAYOS_CHECKSUM_KEY)


def create_payment_link(order_code: str, amount: int, description: str, return_url: str, cancel_url: str):
    """Tạo payment link payOS."""
    if not is_configured():
        return None, "Chưa cấu hình payOS. Vui lòng bổ sung API key."

    data = {
        "orderCode": order_code,
        "amount": amount,
        "description": description,
        "returnUrl": return_url,
        "cancelUrl": cancel_url,
    }
    signature = _signature(data)

    headers = {
        "x-client-id": PAYOS_CLIENT_ID,
        "x-api-key": PAYOS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {**data, "signature": signature}

    try:
        resp = requests.post(
            f"{PAYOS_API_URL}/v2/payment-requests",
            headers=headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == "00":
            return result["data"]["checkoutUrl"], None
        return None, result.get("desc", "payOS trả lỗi không xác định.")
    except requests.RequestException as e:
        logger.error("payOS create_payment_link error: %s", e)
        return None, f"Lỗi kết nối payOS: {e}"


def verify_webhook(payload: dict) -> bool:
    """Verify chữ ký webhook từ payOS."""
    if not is_configured():
        return False

    signature = payload.get("signature", "")
    data = payload.get("data", {})
    expected = _signature(data)
    return hmac.compare_digest(signature, expected)