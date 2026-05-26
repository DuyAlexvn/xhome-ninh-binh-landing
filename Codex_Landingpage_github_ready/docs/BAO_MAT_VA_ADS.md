# Bao mat va san sang chay ads

## Khong duoc dua len GitHub

- `.streamlit/secrets.toml`
- `.env`
- File JSON key Google Cloud
- Log co thong tin khach hang
- Export Google Sheet chua lead

## Du lieu form

Form hien thu cac truong:

- Thoi gian gui
- Ho ten
- Khu vuc xay dung
- Dien tich du kien
- So tang du kien
- Hang muc quan tam
- Thoi gian trien khai
- Ngan sach du kien
- So dien thoai/Zalo

App da co:

- Gioi han do dai truong nhap.
- Validate so dien thoai/Zalo.
- Chan Google Sheets formula injection voi gia tri bat dau bang `=`, `+`, `-`, `@`.
- Khong dua du lieu lead len URL/query string.
- Token bao mat khi gui qua Apps Script.

## Footer nen co truoc khi chay ads

- Ten van phong/cong ty.
- Dia chi van phong.
- Hotline.
- Email.
- Ma so thue/phap ly neu co.
- Link chinh sach bao mat neu deploy public quy mo lon.

## Apps Script

Moi landing nen co token rieng:

```javascript
const SECRET_TOKEN = 'CHANGE_THIS_TO_A_LONG_RANDOM_SECRET';
```

Sau khi sua code Apps Script, luon deploy version moi:

1. Deploy -> Manage deployments.
2. Edit.
3. Version -> New version.
4. Deploy.

## Deploy server

- Bat HTTPS.
- Khong expose file secrets qua static route.
- Khong copy `.streamlit/secrets.toml` vao GitHub.
- Neu dung VPS, chi de port app noi bo sau Nginx khi co the.

## Kiem tra nhanh

```powershell
python tools\validate_landing.py
python -m py_compile app.py Landingpage.py
```

Neu test lead thanh cong, Apps Script phai tra:

```json
{"ok": true}
```
