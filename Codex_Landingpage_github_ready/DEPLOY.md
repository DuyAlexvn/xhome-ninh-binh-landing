# Chỉnh sửa và deploy landing page

## Cấu trúc dự án

```text
Codex_Landingpage/
  app.py
  Landingpage.py
  requirements.txt
  Dockerfile
  docker-compose.yml
  deploy/nginx-xhome.example.conf
  .gitignore
  .dockerignore

  .streamlit/
    config.toml
    secrets.example.toml

  content/
    content.json

  static/
    images/
      brand/
      hero/
      features/
      projects/

  styles/
    landing.css
```

## Chỉnh sửa nội dung

Sửa nội dung trong `content/content.json`.

Các vùng chính:

- `meta`: tiêu đề tab trình duyệt.
- `brand`, `nav`, `top_offer`, `mobile_cta`: phần đầu trang.
- `hero`: headline, subtitle và ảnh chính.
- `features`: 3 card lợi ích.
- `trust_band`: section thống kê.
- `projects`: danh sách dự án.
- `process`: quy trình.
- `faq`: câu hỏi thường gặp.
- `form`: nhãn form và thông báo sau khi gửi.
- `footer`: thông tin cuối trang.

Sau khi lưu file, Streamlit local sẽ tự reload.

## Thay ảnh

Đặt ảnh vào `static/images/`, rồi sửa đường dẫn tương ứng trong `content/content.json`.

Ví dụ:

```json
"image": "static/images/projects/project-moi.jpg"
```

Có thể dùng link ảnh ngoài:

```json
"image": "https://example.com/hero.jpg"
```

Nếu đường dẫn ảnh sai hoặc file chưa tồn tại, landing page vẫn chạy bằng nền CSS dự phòng.

Khuyến nghị production:

- Không dùng đường dẫn local như `C:\Users\...\Desktop\...`.
- Không để ảnh production nằm ngoài repo nếu muốn deploy ổn định.
- Nên đặt ảnh theo nhóm: `static/images/hero/`, `static/images/features/`, `static/images/projects/`, `static/images/brand/`.

## Chỉnh giao diện

CSS nằm trong `styles/landing.css`.

Không cần sửa `app.py` nếu chỉ thay màu sắc, khoảng cách, font-size hoặc responsive layout.

## Chạy local

```powershell
cd Codex_Landingpage
python -m streamlit run app.py --server.port 8501 --server.enableStaticServing true
```

Hoặc dùng file `run_landingpage.bat`.

Mở:

```text
http://127.0.0.1:8501
```

## Secrets

Không commit `.streamlit/secrets.toml` lên GitHub.

File được commit chỉ nên là:

```text
.streamlit/secrets.example.toml
```

Khi deploy, copy file example thành `.streamlit/secrets.toml` trên server hoặc nhập secrets trong giao diện deploy.

`.gitignore` và `.dockerignore` đã chặn `.streamlit/secrets.toml`, `.env`, log và cache. Không dùng `git add -f` với các file này.

## Kết nối Google Sheet để lưu lead

Form sẽ ghi lead vào Google Sheet nếu đã cấu hình Streamlit secrets.

### Cách khuyến nghị: Google Apps Script Web App

1. Mở Google Sheet nhận lead.
2. Vào `Extensions` -> `Apps Script`.
3. Dán code trong `deploy/apps-script-lead-endpoint.js`.
4. Đổi `SECRET_TOKEN` thành token riêng của landing.
5. Deploy dạng Web App:
   - Execute as: `Me`
   - Who has access: `Anyone`
6. Copy Web App URL vào `.streamlit/secrets.toml`:

```toml
[google_apps_script]
web_app_url = "https://script.google.com/macros/s/.../exec"
token = "TOKEN_RIENG_CUA_LANDING"
```

Nếu thay đổi cột lead trong `app.py`, phải cập nhật `HEADERS` trong Apps Script và deploy version mới.

### Cách dự phòng: Google Cloud service account

1. Tạo Google Sheet và copy Sheet ID trong URL.
2. Tạo Google Cloud service account, tải file JSON key.
3. Share Google Sheet cho email `client_email` của service account với quyền Editor.
4. Copy `.streamlit/secrets.example.toml` thành `.streamlit/secrets.toml`.
5. Điền `spreadsheet_id` và các thông tin trong file JSON key vào `secrets.toml`.

Dữ liệu form được ghi theo danh sách cột cố định trong `app.py`, không nhận tên cột từ người dùng. App cũng sanitize dữ liệu trước khi ghi để tránh Google Sheets formula injection, ví dụ các giá trị bắt đầu bằng `=`, `+`, `-`, `@`.

Streamlit form không đưa thông tin khách hàng lên URL. Không thêm logic đọc lead từ query string nếu không thật sự cần.

## Gắn Meta Pixel và GA4

Điền ID tracking trong `.streamlit/secrets.toml`:

```toml
[tracking]
meta_pixel_id = "PASTE_META_PIXEL_ID"
ga4_measurement_id = "G-XXXXXXXXXX"
```

Landing page sẽ gửi:

- `PageView` khi người dùng mở trang.
- `TimeOnPage` / `time_on_page` tại các mốc 15, 30, 60 và 120 giây.
- `Lead` / `lead_submit` sau khi form hợp lệ và lead được lưu thành công.

## Up GitHub

Trước khi commit:

```powershell
cd Codex_Landingpage
python -m py_compile app.py Landingpage.py
```

Kiểm tra không commit các file sau:

- `.streamlit/secrets.toml`
- `*.log`
- `__pycache__/`
- `.venv/`

Các file này đã được chặn bằng `.gitignore`.

## Deploy nhanh lên Streamlit Community Cloud

Streamlit Community Cloud phù hợp nếu cần link public nhanh. App sẽ chạy dưới subdomain dạng `*.streamlit.app`.

Các bước:

1. Đẩy thư mục `Codex_Landingpage` lên GitHub.
2. Vào Streamlit Community Cloud.
3. Chọn repo, branch và main file: `Codex_Landingpage/app.py`.
4. Thêm secrets trong phần app settings nếu dùng Google Sheet, Meta Pixel hoặc GA4.

## Deploy với tên miền riêng

Để dùng tên miền riêng như `xhome-ninhbinh.vn`, nên deploy trên VPS rồi trỏ domain qua Nginx.

### 1. Trên VPS

```bash
cd /opt
git clone <repo-cua-ban> xhome-landingpage
cd xhome-landingpage/Codex_Landingpage
docker compose up -d --build
```

App chạy nội bộ tại port `8501`.

### 2. Trỏ DNS

Trong trang quản lý domain, tạo bản ghi:

```text
A     @      <IP_VPS>
A     www    <IP_VPS>
```

### 3. Cấu hình Nginx

Copy `deploy/nginx-xhome.example.conf` sang server block của Nginx, thay:

```nginx
server_name example.com www.example.com;
```

bằng domain thật.

Sau đó reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Bật HTTPS

Nếu dùng Certbot:

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

Thay `example.com` bằng domain thật.
