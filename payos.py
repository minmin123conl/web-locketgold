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
    """Tạo signature theo chuẩn payOS.

    PayOS SDK dùng `create_signature_of_payment_request`:
    - Thứ tự field cố định: amount, cancelUrl, description, orderCode, returnUrl
    - Không URL-encode giá trị
    - Nối bằng dấu &
    """
    required_fields = ["amount", "cancelUrl", "description", "orderCode", "returnUrl"]
    values = []
    for field in required_fields:
        if field not in data:
            return ""
        values.append(f"{field}={data[field]}")
    data_string = "&".join(values)
    return hmac.new(
        PAYOS_CHECKSUM_KEY.encode("utf-8"),
        data_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def is_configured() -> bool:
    """Kiểm tra đã cấu hình payOS chưa."""
    return bool(PAYOS_CLIENT_ID and PAYOS_API_KEY and PAYOS_CHECKSUM_KEY)


def get_payment_status(order_code: str):
    """Truy vấn trạng thái payment request từ payOS.

    Dùng làm fallback khi webhook không tới (chưa cấu hình URL webhook trên
    dashboard, hoặc bị timeout): khi user quay về returnUrl, server chủ động
    hỏi payOS xem đơn đã thanh toán chưa.

    Trả về (payment_info, error):
    - payment_info: dict dữ liệu payOS (có field "status") nếu thành công
    - error: thông báo lỗi nếu thất bại
    """
    if not is_configured():
        return None, "Chưa cấu hình payOS."

    headers = {
        "x-client-id": PAYOS_CLIENT_ID,
        "x-api-key": PAYOS_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        resp = requests.get(
            f"{PAYOS_API_URL}/v2/payment-requests/{order_code}",
            headers=headers,
            timeout=15,
        )
        # 404 = đơn không tồn tại trên payOS
        if resp.status_code == 404:
            return None, "Không tìm thấy đơn trên payOS."
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == "00":
            return result.get("data", {}), None
        return None, result.get("desc", "payOS trả lỗi không xác định.")
    except requests.RequestException as e:
        logger.error("payOS get_payment_status error: %s", e)
        return None, f"Lỗi kết nối payOS: {e}"


def create_payment_link(order_code: str, amount: int, description: str, return_url: str, cancel_url: str):
    """Tạo payment link payOS."""
    if not is_configured():
        return None, "Chưa cấu hình payOS. Vui lòng bổ sung API key."

    # PayOS yêu cầu orderCode là số nguyên (int), không phải chuỗi
    data = {
        "orderCode": int(order_code),
        "amount": int(amount),
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


def _serialize_obj(data: dict, null_token: str) -> str:
    """Tạo chuỗi ký từ một object theo đúng cách payOS SDK làm.

    SDK (JS) sắp xếp key theo alphabet rồi nối `${key}=${value}` bằng '&'.
    Lưu ý: KHÁC với `_signature()` (dùng cho create payment request, chỉ 5
    field cố định). Webhook ký trên TOÀN BỘ object `data`.
    """
    parts = []
    for key in sorted(data.keys()):
        value = data[key]
        if value is None:
            value = null_token
        elif isinstance(value, bool):
            value = "true" if value else "false"
        elif isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        parts.append(f"{key}={value}")
    return "&".join(parts)


def _signature_from_obj(data: dict, null_token: str) -> str:
    return hmac.new(
        PAYOS_CHECKSUM_KEY.encode("utf-8"),
        _serialize_obj(data, null_token).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_webhook(payload: dict) -> bool:
    """Verify chữ ký webhook từ payOS.

    payOS ký HMAC-SHA256 trên object `data` (không phải 5 field như khi
    tạo payment request). Một số field có thể null; các phiên bản SDK/JSON
    serialize null khác nhau ('null', rỗng, hoặc bỏ hẳn key) nên thử vài
    biến thể. An toàn: kẻ tấn công không có checksum key thì không thể tạo
    được HMAC hợp lệ cho bất kỳ biến thể nào.
    """
    if not is_configured():
        return False

    signature = payload.get("signature", "")
    data = payload.get("data", {})
    if not signature or not isinstance(data, dict) or not data:
        return False

    candidates = [
        _signature_from_obj(data, "null"),
        _signature_from_obj(data, ""),
    ]
    # Biến thể: bỏ hẳn các key có giá trị null
    filtered = {k: v for k, v in data.items() if v is not None}
    candidates.append(_signature_from_obj(filtered, ""))

    return any(hmac.compare_digest(signature, c) for c in candidates)
