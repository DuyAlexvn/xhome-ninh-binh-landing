# Static assets

Ảnh production đặt trong `static/images/`.

Streamlit đang bật static file serving trong `.streamlit/config.toml`, nên các file trong `static/` được phục vụ qua URL `/app/static/...`.

Ví dụ khai báo trong `content/content.json`:

```json
"image": "static/images/projects/project-moi.jpg"
```

Khuyến nghị kích thước:

- Hero: 1600x900 hoặc 1920x1080.
- Feature card: 900x600.
- Project card: 1200x900 hoặc 1600x1200.

Định dạng nên dùng: `.jpg`, `.png`, `.webp`.
