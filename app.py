#!/usr/bin/env python3
"""web-locketgold — Web tool kich hoat Locket Gold.

Ket hop co che tu locketgold.py (inject receipt) va phan server/config
tu server.js + rc_fake_worker.js + mobileconfig de giu Gold.

Chay:  python3 -I app.py     ->  http://127.0.0.1:8787
"""
import asyncio
import json
import re
import time
import os
from datetime import datetime, timezone

import aiohttp
from flask import (
    Flask, jsonify, render_template, request, send_file, Response,
    redirect, url_for, session, flash, abort
)

from config import (
    SECRET_KEY, CREDIT_PRICE, SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE, PERMANENT_SESSION_LIFETIME,
    RATE_LIMIT_LOGIN, RATE_LIMIT_REGISTER, RATE_LIMIT_INJECT,
    RATE_LIMIT_RESOLVE, RATE_LIMIT_TOPUP,
)
from database import db, init_db, User, Transaction, GoldOrder, SupportTicket
from auth import login_required, admin_required, get_current_user, register_user, login_user
from wallet import (
    create_topup_transaction,
    mark_topup_success,
    buy_credit,
    use_credit,
    refund_credit,
    get_transactions,
)
from security import (
    rate_limit, csrf_protect, generate_csrf_token,
    add_security_headers, validate_uid, validate_amount,
)
import payos

HERE = os.path.dirname(os.path.abspath(__file__))
LOCKET_GOLD_DIR = os.path.join(os.path.dirname(HERE), "locket-gold")

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = SESSION_COOKIE_SAMESITE
app.config["SESSION_COOKIE_SECURE"] = SESSION_COOKIE_SECURE
app.config["PERMANENT_SESSION_LIFETIME"] = PERMANENT_SESSION_LIFETIME
init_db(app)

# ════════════════════════════════════════════════════════════════════
# SECURITY: Apply headers to all responses
# ════════════════════════════════════════════════════════════════════
@app.after_request
def apply_security_headers(response):
    return add_security_headers(response)


# ════════════════════════════════════════════════════════════════════
# TEMPLATE CONTEXT: Inject CSRF token
# ════════════════════════════════════════════════════════════════════
@app.context_processor
def inject_csrf_token():
    return {"csrf_token": generate_csrf_token()}


# ════════════════════════════════════════════════════════════════════
# CẤU HÌNH TỰ NHẬP (từ locketgold.py)
# ════════════════════════════════════════════════════════════════════
TOKEN_CONFIG = {
    "name": "Xoăn Gold",
    "fetch_token": "REPLACE_WITH_REAL_TOKEN",
    "app_transaction": "REPLACE_WITH_REAL_APP_TRANSACTION",
    "hash_params": "app_user_id,fetch_token,app_transaction:sha256:8b6cce125219e2c6a26689448234c8c03894cb72855b73e8598c58ed1056d8df",
    "hash_headers": "X-Is-Sandbox:sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa",
    "is_sandbox": False,
    "transaction_id": "",
}

HEADERS = {
    'Host': 'api.revenuecat.com',
    'Authorization': 'Bearer REPLACE_WITH_REAL_API_KEY',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'X-Platform': 'iOS',
    'X-Platform-Version': 'Version 26.2 (Build 23C55)',
    'X-Platform-Device': 'iPhone15,3',
    'X-Platform-Flavor': 'native',
    'X-Version': '5.41.0',
    'X-Client-Version': '2.32.2',
    'X-Client-Bundle-ID': 'com.locket.Locket',
    'X-Client-Build-Version': '3',
    'X-StoreKit2-Enabled': 'true',
    'X-StoreKit-Version': '2',
    'X-Observer-Mode-Enabled': 'false',
    'X-Is-Sandbox': 'false',
    'X-Storefront': 'VNM',
    'X-Apple-Device-Identifier': '39A73C25-1E05-4350-ADA7-5CD3FE1079E8',
    'X-Preferred-Locales': 'vi_KR,ko_KR,en_KR',
    'X-Nonce': 'w0Mlb6+AmV4WYuVv',
    'X-Is-Backgrounded': 'false',
    'X-Retry-Count': '0',
    'X-Is-Debug-Build': 'false',
    'User-Agent': 'Locket/3 CFNetwork/3860.300.31 Darwin/25.2.0',
    'Accept-Language': 'vi-VN,vi;q=0.9',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'X-RevenueCat-ETag': ''
}

# ════════════════════════════════════════════════════════════════════
# CORE LOGIC (từ locketgold.py)
# ════════════════════════════════════════════════════════════════════
async def resolve_uid(username):
    """Phân giải username hoặc link Locket thành UID 28 ký tự"""
    url = f"https://locket.cam/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        "Accept": "text/html"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, allow_redirects=True, timeout=10) as res:
                html = await res.text()
                redirect_url = str(res.url)

                def extract(text):
                    if not text: return None
                    m = re.search(r'/invites/([A-Za-z0-9]{28})', text)
                    if m: return m.group(1)
                    
                    lp = re.search(r'link=([^\s"\'>]+)', text)
                    if lp:
                        try:
                            d = lp.group(1).replace('%3A', ':').replace('%2F', '/')
                            dm = re.search(r'/invites/([A-Za-z0-9]{28})', d)
                            if dm: return dm.group(1)
                        except:
                            pass
                    return None

                return extract(redirect_url) or extract(html)
    except Exception as e:
        return None

async def check_status(uid):
    """Kiểm tra trạng thái Gold hiện tại của UID"""
    url = f"https://api.revenuecat.com/v1/subscribers/{uid}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=10) as res:
                if 200 <= res.status < 300:
                    data = await res.json()
                    entitlements = data.get('subscriber', {}).get('entitlements', {}).get('Gold', {})
                    if entitlements:
                        expires_date = entitlements.get('expires_date')
                        return {"active": True, "expires": expires_date}
                    return {"active": False}
                return {"active": False}
    except Exception:
        return None

async def inject_gold(uid, token_config):
    """Tiêm gói kích hoạt Gold sang tài khoản đích với thông số tự nhập"""
    url = "https://api.revenuecat.com/v1/receipts"
    
    fetch_token = token_config['fetch_token']
    app_transaction = token_config['app_transaction']
    is_sandbox = token_config['is_sandbox']
    
    body = {
        "product_id": "locket_199_1m", 
        "fetch_token": fetch_token, 
        "app_transaction": app_transaction,
        "app_user_id": uid, 
        "is_restore": True, 
        "store_country": "VNM", 
        "currency": "USD",
        "price": "1.99", 
        "normal_duration": "P1M", 
        "subscription_group_id": "21419447",
        "observer_mode": False, 
        "initiation_source": "restore", 
        "offers": [],
        "attributes": { 
            "$attConsentStatus": { "updated_at_ms": int(time.time() * 1000), "value": "notDetermined" } 
        }
    }
    
    current_headers = HEADERS.copy()
    current_headers['Content-Length'] = str(len(json.dumps(body)))
    
    if token_config.get('hash_params'):
        current_headers['X-Post-Params-Hash'] = token_config['hash_params']
    if token_config.get('hash_headers'):
        current_headers['X-Headers-Hash'] = token_config['hash_headers']
    
    current_headers['X-Is-Sandbox'] = str(is_sandbox).lower()

    async with aiohttp.ClientSession() as session:
        for attempt in range(5):
            try:
                async with session.post(url, headers=current_headers, json=body, timeout=15) as res:
                    status_code = res.status
                    
                    if status_code == 200:
                        status = await check_status(uid)
                        if status and status.get('active'):
                            return {"success": True, "message": "Kích hoạt Locket Gold thành công!", "expires": status.get('expires')}
                        else:
                            await asyncio.sleep(2)
                            status = await check_status(uid)
                            if status and status.get('active'):
                                return {"success": True, "message": "Kích hoạt thành công sau khi chờ xác thực!", "expires": status.get('expires')}
                            return {"success": False, "message": "Thất bại: Server chấp nhận nhưng chưa cấp quyền Gold."}
                            
                    elif status_code == 529:
                        await asyncio.sleep(2)
                        continue
                        
                    else:
                        msg = "Lỗi không xác định"
                        try:
                            resp_json = await res.json()
                            msg = resp_json.get('message', str(status_code))
                        except:
                            msg = str(status_code)
                        return {"success": False, "message": f"Bị từ chối: {msg}"}
                        
            except Exception as e:
                if attempt == 4:
                    return {"success": False, "message": f"Lỗi mạng: {e}"}
                await asyncio.sleep(2)
    
    return {"success": False, "message": "Thất bại sau 5 lần thử."}

# ════════════════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    current_user = get_current_user()
    return render_template("index.html", current_user=current_user)


@app.route("/api/resolve", methods=["POST"])
@rate_limit("resolve", limit=RATE_LIMIT_RESOLVE, window_seconds=3600)
@csrf_protect
def api_resolve():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"ok": False, "error": "Vui lòng nhập username hoặc link."}), 400
    
    uid = asyncio.run(resolve_uid(username))
    if not uid:
        return jsonify({"ok": False, "error": "Không tìm thấy UID."}), 404
    
    return jsonify({"ok": True, "uid": uid})


@app.route("/api/status/<uid>", methods=["GET"])
def api_status(uid):
    status = asyncio.run(check_status(uid))
    if status is None:
        return jsonify({"ok": False, "error": "Không thể kiểm tra trạng thái."}), 500
    return jsonify({"ok": True, "status": status})


@app.route("/api/config", methods=["GET"])
def api_config():
    """Trả về thông tin cấu hình hiện tại (không bao gồm token)"""
    return jsonify({
        "name": TOKEN_CONFIG.get("name", ""),
        "is_sandbox": TOKEN_CONFIG.get("is_sandbox", False),
        "has_fetch_token": bool(TOKEN_CONFIG.get("fetch_token")),
        "has_app_transaction": bool(TOKEN_CONFIG.get("app_transaction")),
        "has_hash_params": bool(TOKEN_CONFIG.get("hash_params")),
        "has_hash_headers": bool(TOKEN_CONFIG.get("hash_headers")),
    })


# ════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ════════════════════════════════════════════════════════════════════
@app.route("/dang-ky", methods=["GET", "POST"])
@rate_limit("register", limit=RATE_LIMIT_REGISTER, window_seconds=3600)
@csrf_protect
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        if not username or not email or not password:
            flash("Vui lòng điền đầy đủ thông tin.", "error")
            return render_template("dang-ky.html")

        if password != confirm:
            flash("Mật khẩu xác nhận không khớp.", "error")
            return render_template("dang-ky.html")

        user, error = register_user(username, email, password)
        if error:
            flash(error, "error")
            return render_template("dang-ky.html")

        session["user_id"] = user.id
        flash("Đăng ký thành công!", "success")
        return redirect(url_for("index"))

    return render_template("dang-ky.html")


@app.route("/dang-nhap", methods=["GET", "POST"])
@rate_limit("login", limit=RATE_LIMIT_LOGIN, window_seconds=900)
@csrf_protect
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user, error = login_user(username, password)
        if error:
            flash(error, "error")
            return render_template("dang-nhap.html")

        session["user_id"] = user.id
        flash("Đăng nhập thành công!", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("index"))

    return render_template("dang-nhap.html")


@app.route("/dang-xuat")
def logout():
    session.clear()
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("index"))


# ════════════════════════════════════════════════════════════════════
# WALLET ROUTES
# ════════════════════════════════════════════════════════════════════
@app.route("/vi")
@login_required
def wallet_page():
    user = get_current_user()
    transactions = get_transactions(user.id)
    return render_template("vi.html", user=user, transactions=transactions, CREDIT_PRICE=CREDIT_PRICE)


@app.route("/api/wallet", methods=["GET"])
@login_required
def api_wallet():
    user = get_current_user()
    return jsonify({"ok": True, "user": user.to_dict()})


@app.route("/api/wallet/topup", methods=["POST"])
@login_required
@rate_limit("topup", limit=RATE_LIMIT_TOPUP, window_seconds=3600)
@csrf_protect
def api_topup():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    amount, error = validate_amount(data.get("amount"))
    if error:
        return jsonify({"ok": False, "error": error}), 400

    tx = create_topup_transaction(user.id, amount)
    return_url = request.host_url.rstrip("/") + "/vi?status=success"
    cancel_url = request.host_url.rstrip("/") + "/vi?status=cancelled"

    checkout_url, error = payos.create_payment_link(
        order_code=tx.order_code,
        amount=amount,
        description=f"toi tra tien nhe",
        return_url=return_url,
        cancel_url=cancel_url,
    )

    if error:
        # Nếu chưa cấu hình payOS, vẫn trả về order_code để test
        return jsonify({
            "ok": False,
            "error": error,
            "order_code": tx.order_code,
            "amount": amount,
        }), 400

    return jsonify({"ok": True, "checkout_url": checkout_url, "order_code": tx.order_code})


@app.route("/api/wallet/buy-credit", methods=["POST"])
@login_required
@csrf_protect
def api_buy_credit():
    user = get_current_user()
    tx, error = buy_credit(user)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    return jsonify({"ok": True, "user": user.to_dict(), "transaction": tx.to_dict()})


@app.route("/api/wallet/transactions", methods=["GET"])
@login_required
def api_transactions():
    user = get_current_user()
    transactions = get_transactions(user.id)
    return jsonify({"ok": True, "transactions": [t.to_dict() for t in transactions]})


# ════════════════════════════════════════════════════════════════════
# PAYOS WEBHOOK
# ════════════════════════════════════════════════════════════════════
@app.route("/api/payos/webhook", methods=["POST"])
def payos_webhook():
    payload = request.get_json(silent=True) or {}
    if not payos.verify_webhook(payload):
        return jsonify({"ok": False, "error": "Chữ ký không hợp lệ."}), 400

    data = payload.get("data", {})
    order_code = data.get("orderCode")
    status = data.get("status", "")

    if status == "PAID" and order_code:
        # PayOS trả orderCode dạng int, cần chuyển sang str để query DB
        tx, error = mark_topup_success(str(order_code))
        if error:
            return jsonify({"ok": False, "error": error}), 400

    return jsonify({"ok": True})


# ════════════════════════════════════════════════════════════════════
# GOLD ACTIVATION (yêu cầu đăng nhập)
# ════════════════════════════════════════════════════════════════════
@app.route("/api/inject", methods=["POST"])
@login_required
@rate_limit("inject", limit=RATE_LIMIT_INJECT, window_seconds=3600)
@csrf_protect
def api_inject():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    uid = (data.get("uid") or "").strip()
    if not uid:
        return jsonify({"ok": False, "error": "Thiếu UID."}), 400

    # Validate UID
    ok, error = validate_uid(uid)
    if not ok:
        return jsonify({"ok": False, "error": error}), 400

    # Trừ 1 credit trước
    ok, error = use_credit(user)
    if not ok:
        return jsonify({"ok": False, "error": error}), 400

    result = asyncio.run(inject_gold(uid, TOKEN_CONFIG))

    if result.get("success"):
        # Ghi nhận gold order
        order = GoldOrder(user_id=user.id, uid=uid, status="success")
        db.session.add(order)
        tx = Transaction(
            user_id=user.id,
            type="activate_gold",
            amount=0,
            status="success",
            description=f"Kích hoạt Gold cho UID {uid}",
        )
        db.session.add(tx)
        db.session.commit()
        result["message"] = "Kích hoạt Locket Gold thành công! Lượt đã được trừ."
    else:
        # Hoàn lại credit
        refund_credit(user)
        order = GoldOrder(user_id=user.id, uid=uid, status="failed")
        db.session.add(order)
        db.session.commit()
        # Cải thiện thông báo lỗi
        error_msg = result.get("message", "Kích hoạt thất bại.")
        result["message"] = f"{error_msg} Lượt đã được hoàn lại."
        result["refunded"] = True

    return jsonify(result)


# ════════════════════════════════════════════════════════════════════
# SUPPORT ROUTES
# ════════════════════════════════════════════════════════════════════
@app.route("/ho-tro", methods=["GET", "POST"])
@login_required
@csrf_protect
def support_page():
    user = get_current_user()
    if request.method == "POST":
        subject = (request.form.get("subject") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not subject or not message:
            flash("Vui lòng điền đầy đủ thông tin.", "error")
            return render_template("ho-tro.html", user=user, tickets=user.support_tickets)

        ticket = SupportTicket(
            user_id=user.id,
            subject=subject,
            message=message,
            status="open",
        )
        db.session.add(ticket)
        db.session.commit()
        flash("Gửi yêu cầu hỗ trợ thành công!", "success")
        return redirect(url_for("support_page"))

    tickets = SupportTicket.query.filter_by(user_id=user.id).order_by(SupportTicket.created_at.desc()).all()
    return render_template("ho-tro.html", user=user, tickets=tickets)


@app.route("/api/support/tickets", methods=["GET"])
@login_required
def api_support_tickets():
    user = get_current_user()
    tickets = SupportTicket.query.filter_by(user_id=user.id).order_by(SupportTicket.created_at.desc()).all()
    return jsonify({"ok": True, "tickets": [t.to_dict() for t in tickets]})


@app.route("/api/support/tickets", methods=["POST"])
@login_required
@csrf_protect
def api_create_ticket():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    message = (data.get("message") or "").strip()

    if not subject or not message:
        return jsonify({"ok": False, "error": "Vui lòng điền đầy đủ thông tin."}), 400

    ticket = SupportTicket(
        user_id=user.id,
        subject=subject,
        message=message,
        status="open",
    )
    db.session.add(ticket)
    db.session.commit()
    return jsonify({"ok": True, "ticket": ticket.to_dict()})


# ════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ════════════════════════════════════════════════════════════════════
@app.route("/admin")
@admin_required
def admin_page():
    return render_template("admin.html")


@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def api_admin_stats():
    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    total_gold_orders = GoldOrder.query.count()
    total_tickets = SupportTicket.query.count()
    total_revenue = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.status == "success").scalar() or 0

    return jsonify({
        "ok": True,
        "stats": {
            "total_users": total_users,
            "total_transactions": total_transactions,
            "total_gold_orders": total_gold_orders,
            "total_tickets": total_tickets,
            "total_revenue": float(total_revenue),
        }
    })


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def api_admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"ok": True, "users": [u.to_dict() for u in users]})


@app.route("/api/admin/users/<int:user_id>", methods=["PATCH"])
@admin_required
@csrf_protect
def api_admin_update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"ok": False, "error": "Không tìm thấy user."}), 404

    data = request.get_json(silent=True) or {}
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])
    if "balance" in data:
        try:
            user.balance = int(data["balance"])
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Số dư không hợp lệ."}), 400
    if "credits" in data:
        try:
            user.credits = int(data["credits"])
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Số lượt không hợp lệ."}), 400

    db.session.commit()
    return jsonify({"ok": True, "user": user.to_dict()})


@app.route("/api/admin/transactions", methods=["GET"])
@admin_required
def api_admin_transactions():
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(100).all()
    return jsonify({"ok": True, "transactions": [t.to_dict() for t in transactions]})


@app.route("/api/admin/gold-orders", methods=["GET"])
@admin_required
def api_admin_gold_orders():
    orders = GoldOrder.query.order_by(GoldOrder.created_at.desc()).limit(100).all()
    return jsonify({"ok": True, "orders": [o.to_dict() for o in orders]})


@app.route("/api/admin/tickets", methods=["GET"])
@admin_required
def api_admin_tickets():
    tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    return jsonify({"ok": True, "tickets": [t.to_dict() for t in tickets]})


@app.route("/api/admin/tickets/<int:ticket_id>", methods=["PATCH"])
@admin_required
@csrf_protect
def api_admin_update_ticket(ticket_id):
    ticket = db.session.get(SupportTicket, ticket_id)
    if not ticket:
        return jsonify({"ok": False, "error": "Không tìm thấy ticket."}), 404

    data = request.get_json(silent=True) or {}
    if "status" in data:
        ticket.status = data["status"]
    if "admin_reply" in data:
        ticket.admin_reply = data["admin_reply"]

    db.session.commit()
    return jsonify({"ok": True, "ticket": ticket.to_dict()})


# ════════════════════════════════════════════════════════════════════
# SERVE CONFIG FILES (từ locket-gold/)
# ════════════════════════════════════════════════════════════════════
@app.route("/download/mobileconfig")
def download_mobileconfig():
    """Tải file cấu hình locketgold_novpn.mobileconfig để giữ Gold"""
    filepath = os.path.join(LOCKET_GOLD_DIR, "locketgold_novpn.mobileconfig")
    if not os.path.exists(filepath):
        return jsonify({"error": "File không tồn tại trên server"}), 404
    
    return send_file(filepath, as_attachment=True, download_name="locketgold_novpn.mobileconfig")


if __name__ == "__main__":
    print("=" * 62)
    print(" web-locketgold — Web tool kich hoat Locket Gold")
    print(" -> http://0.0.0.0:8787")
    print("=" * 62)
    app.run(host="0.0.0.0", port=8787, debug=False)