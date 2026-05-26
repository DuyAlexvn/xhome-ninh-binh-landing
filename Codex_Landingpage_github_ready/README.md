# XHOME Ninh Bình Landing Page

Landing page Streamlit cho XHOME Ninh Bình, tách riêng nội dung, ảnh, CSS và cấu hình deploy.

## Chạy local

```powershell
cd Codex_Landingpage
python -m streamlit run app.py --server.port 8501 --server.enableStaticServing true
```

Mở `http://127.0.0.1:8501`.

## Nhân bản landing mới

Tài liệu nhân bản nằm ở `docs/NHAN_BAN_LANDING.md`.

Các file thường cần sửa cho landing mới:

- `content/content.json`: nội dung, dự án, form, footer.
- `static/images/`: ảnh production.
- `styles/landing.css`: giao diện.
- `.streamlit/secrets.toml`: Apps Script URL/token, tracking IDs. Không commit file này.

Chạy kiểm tra trước khi deploy:

```powershell
python tools\validate_landing.py
python -m py_compile app.py Landingpage.py
python -m json.tool content\content.json
```

## Sửa nội dung

- Copy/form/dự án: `content/content.json`
- Giao diện/CSS: `styles/landing.css`
- Ảnh: `static/images/`
- Secrets mẫu: `.streamlit/secrets.example.toml`

Không commit `.streamlit/secrets.toml`.

## Bảo mật và dữ liệu

- Ảnh production phải nằm trong `static/images/` và được trỏ bằng đường dẫn tương đối trong `content/content.json`.
- Không dùng đường dẫn kiểu `C:\...` hoặc ảnh chỉ có trên máy local.
- Form gửi bằng Streamlit form state, không đưa thông tin khách hàng lên URL/query string.
- Google Apps Script Web App URL/token hoặc Google Sheet service account chỉ nằm trong `.streamlit/secrets.toml` trên server.
- Trước khi ghi Google Sheet, app giới hạn độ dài, validate số điện thoại và chặn Google Sheets formula injection.

Apps Script mẫu để nhận lead nằm ở `deploy/apps-script-lead-endpoint.js`.

## Deploy

Xem chi tiết trong `DEPLOY.md`.
