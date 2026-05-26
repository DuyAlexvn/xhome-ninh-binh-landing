# Huong dan nhan ban landing page

Tai lieu nay dung de tao nhanh mot landing moi tu template hien tai ma van giu duoc bao mat, kha nang deploy va de bao tri.

## 1. Tao ban sao moi

1. Copy thu muc `Codex_Landingpage` sang ten moi, vi du `Landing_XHOME_NamDinh`.
2. Xoa cac file runtime neu co:
   - `__pycache__/`
   - `*.log`
   - `.streamlit/secrets.toml`
3. Tao repo Git rieng cho landing moi.
4. Chay validate:

```powershell
python tools\validate_landing.py
```

## 2. Cac file can sua cho landing moi

- `content/content.json`: toan bo noi dung, cau hoi form, du an, footer.
- `static/images/`: anh production cua landing.
- `styles/landing.css`: giao dien, mau sac, spacing, responsive.
- `.streamlit/secrets.toml`: secrets local/server, khong commit.
- `deploy/apps-script-lead-endpoint.js`: code Google Apps Script mau.

Han che sua `app.py` neu chi thay noi dung, anh, mau sac hoac domain.

## 3. Quy tac anh

- Tat ca anh production phai nam trong `static/images/`.
- Khong dung duong dan local kieu `C:\Users\...\Desktop\...` trong `content.json`.
- Duong dan anh trong `content.json` nen co dang:

```json
"image": "static/images/projects/project-demo.jpg"
```

## 4. Form lead va Google Sheet

Landing hien dung Google Apps Script Web App neu co cau hinh:

```toml
[google_apps_script]
web_app_url = "https://script.google.com/macros/s/.../exec"
token = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
```

Moi landing nen co:

- Google Sheet rieng.
- Token rieng.
- Apps Script deployment rieng.

Neu thay doi cot lead trong `app.py`, phai cap nhat dong `HEADERS` trong `deploy/apps-script-lead-endpoint.js` va Apps Script dang deploy.

## 5. Bao mat secrets

Khong commit cac file sau:

- `.streamlit/secrets.toml`
- `.env`
- log runtime
- file JSON key Google Cloud neu co

`.gitignore` va `.dockerignore` da chan cac file nay. Khong dung `git add -f` voi secrets.

## 6. Checklist truoc khi deploy

```powershell
python tools\validate_landing.py
python -m py_compile app.py Landingpage.py
python -m json.tool content\content.json
```

Kiem tra thu cong:

- Form gui duoc lead vao Google Sheet.
- Sheet co cot `Ho ten` / `Họ tên` dung theo Apps Script.
- Footer co dia chi, hotline, email, ma so thue.
- Chinh sach bao mat duoc bo sung neu chay ads quy mo lon.
- Anh khong bi mat, khong dung link local.
- `.streamlit/secrets.toml` khong nam trong Git.

## 7. Deploy domain rieng

1. Push repo len GitHub.
2. Tren VPS, clone repo va chay Docker:

```bash
docker compose up -d --build
```

3. Tro DNS domain ve IP VPS.
4. Cau hinh Nginx theo `deploy/nginx-xhome.example.conf`.
5. Bat HTTPS bang Certbot.

## 8. Khi can update landing

- Sua noi dung: `content/content.json`.
- Doi anh: them file vao `static/images/`, sua path trong `content.json`.
- Doi giao dien: `styles/landing.css`.
- Doi Sheet nhan lead: update `.streamlit/secrets.toml` tren server.
- Doi cot lead: update ca `app.py` va Apps Script `HEADERS`.
