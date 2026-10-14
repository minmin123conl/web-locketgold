# web-locketgold — Web Tool Kích Hoạt Locket Gold

Web tool kết hợp cơ chế từ `locketgold.py` (inject receipt) và phần server/config từ `server.js` + `rc_fake_worker.js` + `mobileconfig` để kích hoạt và giữ Gold.

## Tính năng

- **Phân giải UID**: Nhập username hoặc link Locket → tự động tìm UID 28 ký tự
- **Kiểm tra trạng thái**: Xem Gold đang hoạt động hay chưa
- **Kích hoạt Gold**: Tiêm gói kích hoạt Gold sang tài khoản đích
- **Tải file cấu hình**: Tải các file server/config để giữ Gold trên thiết bị
- **Đăng ký / Đăng nhập**: Hệ thống tài khoản người dùng
- **Ví điện tử**: Nạp tiền qua payOS, mua lượt kích hoạt
- **Lịch sử giao dịch**: Xem lịch sử nạp tiền, mua hàng
- **Hỗ trợ khách hàng**: Gửi ticket hỗ trợ, xem phản hồi
- **Trang quản trị**: Quản lý người dùng, giao dịch, ticket hỗ trợ

## Chạy

```bash
cd web-locketgold
pip install -r requirements.txt
python3 -I app.py
```

Mở trình duyệt: `http://127.0.0.1:8787`

## Cấu hình payOS

### 1. Đăng ký tài khoản payOS

Truy cập [https://payos.vn](https://payos.vn) và đăng ký tài khoản.

### 2. Lấy API Key

Sau khi đăng ký, vào **Dashboard → Cài đặt → API Keys** để lấy:
- `PAYOS_CLIENT_ID`
- `PAYOS_API_KEY`
- `PAYOS_CHECKSUM_KEY`

### 3. Cấu hình môi trường

Tạo file `.env` trong thư mục `web-locketgold/`:

```bash
# Cấu hình payOS
PAYOS_CLIENT_ID=your_client_id
PAYOS_API_KEY=your_api_key
PAYOS_CHECKSUM_KEY=your_checksum_key

# Cấu hình webhook (tùy chọn)
PAYOS_WEBHOOK_URL=https://your-domain.com/api/payos/webhook

# Cấu hình admin (tùy chọn)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
```

### 4. Cấu hình trong `config.py`

Nếu không dùng `.env`, bạn có thể cấu hình trực tiếp trong `config.py`:

```python
# Cấu hình payOS
PAYOS_CLIENT_ID = "your_client_id"
PAYOS_API_KEY = "your_api_key"
PAYOS_CHECKSUM_KEY = "your_checksum_key"

# Cấu hình webhook (tùy chọn)
PAYOS_WEBHOOK_URL = "https://your-domain.com/api/payos/webhook"

# Cấu hình admin (tùy chọn)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your_secure_password"
```

### 5. Cấu hình webhook (tùy chọn)

Để nhận thông báo thanh toán tự động, cấu hình webhook trong payOS Dashboard:
- URL: `https://your-domain.com/api/payos/webhook`
- Phương thức: `POST`

Nếu không cấu hình webhook, hệ thống sẽ kiểm tra trạng thái giao dịch khi người dùng truy cập trang ví.

## Cấu trúc

```
web-locketgold/
├── app.py                      # Flask backend + core logic
├── config.py                   # Cấu hình ứng dụng
├── database.py                 # Database (SQLite)
├── auth.py                     # Xác thực người dùng
├── security.py                 # Bảo mật (CSRF, rate limiting, headers)
├── payos.py                    # Tích hợp payOS
├── templates/
│   ├── index.html              # Trang chủ
│   ├── vi.html                 # Trang ví
│   ├── dang-ky.html            # Đăng ký
│   ├── dang-nhap.html          # Đăng nhập
│   ├── admin.html              # Trang quản trị
│   └── ho-tro.html             # Trang hỗ trợ
├── static/
│   ├── style.css               # Styles
│   ├── app.js                  # Frontend logic
│   └── wallet.js               # Logic ví
└── README.md
```

## API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/resolve` | Phân giải username → UID |
| GET | `/api/status/<uid>` | Kiểm tra trạng thái Gold |
| POST | `/api/inject` | Kích hoạt Gold cho UID |
| GET | `/api/config` | Thông tin cấu hình hiện tại |
| GET | `/api/files` | Danh sách file cấu hình |
| GET | `/download/<filename>` | Tải file cấu hình |
| POST | `/api/wallet/topup` | Tạo giao dịch nạp tiền |
| POST | `/api/wallet/buy-credit` | Mua lượt kích hoạt |
| GET | `/api/wallet/transactions` | Lịch sử giao dịch |
| POST | `/api/payos/webhook` | Webhook payOS |
| POST | `/api/support/ticket` | Gửi ticket hỗ trợ |
| GET | `/api/support/tickets` | Danh sách ticket của người dùng |
| POST | `/api/admin/users/<id>/toggle` | Khóa/mở khóa người dùng |
| POST | `/api/admin/users/<id>/credits` | Cộng/trừ lượt kích hoạt |
| POST | `/api/admin/tickets/<id>/reply` | Trả lời ticket |
| POST | `/api/admin/tickets/<id>/close` | Đóng ticket |

## Bảo mật

- **CSRF Protection**: Tất cả form và API calls đều có CSRF token
- **Rate Limiting**: Giới hạn số lần request
- **Security Headers**: Các header bảo mật được thêm tự động
- **Input Validation**: Kiểm tra dữ liệu đầu vào
- **Password Hashing**: Mật khẩu được hash bằng bcrypt