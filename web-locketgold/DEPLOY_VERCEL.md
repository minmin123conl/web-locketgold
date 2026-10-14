# Hướng dẫn Deploy web-locketgold lên Vercel

## Bước 1: Chuẩn bị Database (PostgreSQL)

Vercel serverless **không hỗ trợ SQLite** (file system không persistent). Bạn cần dùng PostgreSQL.

### Cách 1: Dùng Vercel Postgres (miễn phí)
1. Vào [vercel.com](https://vercel.com) → Dashboard
2. Chọn project → **Storage** → **Create Database** → **Postgres**
3. Copy `DATABASE_URL` (dạng `postgresql://...`)

### Cách 2: Dùng Neon (miễn phí)
1. Vào [neon.tech](https://neon.tech) → tạo project
2. Copy connection string (dạng `postgresql://...`)

## Bước 2: Deploy lên Vercel

### Cách 1: Deploy qua GitHub (tự động)
1. Vào [vercel.com](https://vercel.com) → **Add New Project**
2. Import repo `minmin123conl/web-locketgold`
3. Vercel sẽ tự nhận diện Python/Flask
4. Cấu hình **Environment Variables** (xem Bước 3)
5. Click **Deploy**

### Cách 2: Deploy qua CLI
```bash
# Cài Vercel CLI
npm install -g vercel

# Đăng nhập
vercel login

# Deploy từ thư mục dự án
cd web-locketgold
vercel --prod
```

## Bước 3: Cấu hình Environment Variables

Trong Vercel Dashboard → Project → **Settings** → **Environment Variables**, thêm:

| Variable | Giá trị | Bắt buộc |
|----------|---------|----------|
| `DATABASE_URL` | `postgresql://...` (từ Bước 1) | ✅ |
| `SECRET_KEY` | Chuỗi ngẫu nhiên dài (vd: `openssl rand -hex 32`) | ✅ |
| `ADMIN_USERNAME` | Tên admin (mặc định: `admin`) | ⚠️ Nên đổi |
| `ADMIN_PASSWORD` | Mật khẩu admin (mặc định: `admin123`) | ⚠️ Nên đổi |
| `PAYOS_CLIENT_ID` | Client ID từ PayOS | ⚠️ Nếu dùng PayOS |
| `PAYOS_API_KEY` | API Key từ PayOS | ⚠️ Nếu dùng PayOS |
| `PAYOS_CHECKSUM_KEY` | Checksum Key từ PayOS | ⚠️ Nếu dùng PayOS |
| `SESSION_COOKIE_SECURE` | `true` (khi deploy HTTPS) | ⚠️ Nên set |

## Bước 4: Cấu hình Vercel

File `vercel.json` đã được tạo sẵn:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

## Bước 5: Kiểm tra sau deploy

Sau khi deploy thành công:
1. Mở URL: `https://web-locketgold.vercel.app`
2. Đăng nhập admin: `/admin` (dùng `ADMIN_USERNAME` / `ADMIN_PASSWORD`)
3. Kiểm tra các trang:
   - `/` - Trang chủ
   - `/dang-ky` - Đăng ký
   - `/dang-nhap` - Đăng nhập
   - `/vi` - Ví
   - `/ho-tro` - Hỗ trợ
   - `/admin` - Admin

## Lưu ý quan trọng

1. **Database**: Vercel serverless không lưu file, phải dùng PostgreSQL
2. **Webhook PayOS**: Cần cấu hình webhook URL trỏ đến `https://web-locketgold.vercel.app/api/payos/webhook`
3. **Mobileconfig**: File `locketgold_novpn.mobileconfig` nằm ở `locket-gold/` - cần upload lên storage hoặc cấu hình lại
4. **Token**: `TOKEN_CONFIG` trong `app.py` chứa token nhạy cảm - nên chuyển sang Environment Variables
5. **Rate limiting**: Có thể bật/tắt qua `RATE_LIMIT_ENABLED`

## Troubleshooting

### Lỗi: `ModuleNotFoundError: No module named 'app'`
- Kiểm tra `api/index.py` có đúng đường dẫn import
- Đảm bảo `app.py` nằm cùng cấp với `api/`

### Lỗi: `sqlite3.OperationalError: unable to open database file`
- Vercel không hỗ trợ SQLite
- Cấu hình `DATABASE_URL` trỏ đến PostgreSQL

### Lỗi: `psycopg2.OperationalError`
- Kiểm tra `DATABASE_URL` đúng định dạng
- Đảm bảo database đã được tạo