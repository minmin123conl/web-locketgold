// ════════════════════════════════════════════════════════════════════
// WALLET PAGE LOGIC
// ════════════════════════════════════════════════════════════════════
(function () {
    "use strict";

    const scriptEl = document.currentScript;
    const CREDIT_PRICE = scriptEl ? parseInt(scriptEl.dataset.creditPrice || "0", 10) : 0;

    const topupAmountInput = document.getElementById("topup-amount");
    const btnTopup = document.getElementById("btn-topup");
    const topupResult = document.getElementById("topup-result");
    const btnBuyCredit = document.getElementById("btn-buy-credit");
    const buyCreditResult = document.getElementById("buy-credit-result");

    // ── Đồng bộ khi quay về từ payOS ─────────────────────────────────
    // Webhook payOS có thể không tới (mạng, cấu hình). Khi returnUrl có
    // ?status=success&order_code=..., chủ động gọi server xác nhận với payOS
    // rồi cộng tiền (idempotent). Không phụ thuộc webhook.
    (async function syncOnReturn() {
        const params = new URLSearchParams(window.location.search);
        if (params.get("status") !== "success") return;
        const orderCode = params.get("order_code");
        if (!orderCode) return;

        let tries = 0;
        const MAX_TRIES = 6;
        const DELAY_MS = 3000;

        async function attempt() {
            tries += 1;
            try {
                const res = await fetch("/api/wallet/sync", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRF-Token": CSRF_TOKEN,
                    },
                    body: JSON.stringify({ order_code: orderCode }),
                });
                const data = await res.json();
                if (data.ok && data.status === "success") {
                    showResult(topupResult, "success", "✅ Nạp tiền thành công!");
                    setTimeout(function () {
                        window.location.replace("/vi");
                    }, 1200);
                    return;
                }
            } catch (err) {
                // im lặng, thử lại
            }
            if (tries < MAX_TRIES) {
                setTimeout(attempt, DELAY_MS);
            } else {
                showResult(
                    topupResult,
                    "error",
                    "⏳ Chưa xác nhận được thanh toán. Vui lòng tải lại trang sau ít phút."
                );
            }
        }
        attempt();
    })();

    function formatVnd(n) {
        return Number(n || 0).toLocaleString("vi-VN") + "đ";
    }

    function showResult(el, type, message) {
        if (!el) return;
        el.className = "result-box result-" + type;
        el.innerHTML = message;
        el.classList.remove("hidden");
    }

    // ── Topup option buttons ─────────────────────────────────────────
    document.querySelectorAll(".topup-option").forEach(function (btn) {
        btn.addEventListener("click", function () {
            document.querySelectorAll(".topup-option").forEach(function (b) {
                b.classList.remove("active");
            });
            btn.classList.add("active");
            if (topupAmountInput) {
                topupAmountInput.value = btn.dataset.amount;
            }
        });
    });

    // ── Topup ────────────────────────────────────────────────────────
    if (btnTopup) {
        btnTopup.addEventListener("click", async function () {
            const amount = parseInt(topupAmountInput ? topupAmountInput.value : "0", 10);
            if (!amount || amount < 1000) {
                showResult(topupResult, "error", "⚠️ Số tiền nạp tối thiểu 1.000đ.");
                return;
            }

            btnTopup.disabled = true;
            const originalText = btnTopup.querySelector(".btn-text").textContent;
            btnTopup.querySelector(".btn-text").textContent = "Đang xử lý...";

            try {
                const res = await fetch("/api/wallet/topup", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "X-CSRF-Token": CSRF_TOKEN
                    },
                    body: JSON.stringify({ amount: amount }),
                });
                const data = await res.json();

                if (data.ok && data.checkout_url) {
                    showResult(topupResult, "success", "✅ Đang chuyển đến trang thanh toán...");
                    window.location.href = data.checkout_url;
                } else {
                    showResult(
                        topupResult,
                        "error",
                        "❌ " + (data.error || "Không thể tạo giao dịch.") +
                            (data.order_code ? " (Mã đơn: " + data.order_code + ")" : "")
                    );
                }
            } catch (err) {
                showResult(topupResult, "error", "❌ Lỗi kết nối: " + err.message);
            } finally {
                btnTopup.disabled = false;
                btnTopup.querySelector(".btn-text").textContent = originalText;
            }
        });
    }

    // ── Buy credit ───────────────────────────────────────────────────
    if (btnBuyCredit) {
        btnBuyCredit.addEventListener("click", async function () {
            btnBuyCredit.disabled = true;
            const originalText = btnBuyCredit.querySelector(".btn-text").textContent;
            btnBuyCredit.querySelector(".btn-text").textContent = "Đang xử lý...";

            try {
                const res = await fetch("/api/wallet/buy-credit", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "X-CSRF-Token": CSRF_TOKEN
                    },
                });
                const data = await res.json();

                if (data.ok) {
                    showResult(
                        buyCreditResult,
                        "success",
                        "✅ Mua thành công! Bạn có " + data.user.credits + " lượt kích hoạt."
                    );
                    setTimeout(function () {
                        window.location.reload();
                    }, 1500);
                } else {
                    showResult(buyCreditResult, "error", "❌ " + (data.error || "Không thể mua lượt."));
                }
            } catch (err) {
                showResult(buyCreditResult, "error", "❌ Lỗi kết nối: " + err.message);
            } finally {
                btnBuyCredit.disabled = false;
                btnBuyCredit.querySelector(".btn-text").textContent = originalText;
            }
        });
    }
})();