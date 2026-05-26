from datetime import datetime
import html
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlparse

import streamlit as st
import streamlit.components.v1 as components


BASE_DIR = Path(__file__).resolve().parent
CONTENT_PATH = BASE_DIR / "content" / "content.json"
LEAD_HEADERS = [
    "Thời gian gửi",
    "Họ tên",
    "Khu vực xây dựng",
    "Diện tích dự kiến",
    "Số tầng dự kiến",
    "Hạng mục quan tâm",
    "Thời gian triển khai",
    "Ngân sách dự kiến",
    "Số điện thoại/Zalo",
]
MAX_FIELD_LENGTH = 300
MAX_BUDGET_LENGTH = 120
MAX_PHONE_LENGTH = 30
SHEET_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
PHONE_PATTERN = re.compile(r"^[0-9+\-\s().]{8,30}$")


def load_content() -> dict:
    with CONTENT_PATH.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_css(path: str) -> None:
    css_path = BASE_DIR / path
    if css_path.exists():
        st.html(f"<style>{css_path.read_text(encoding='utf-8-sig')}</style>")


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def clean_text(value: object, max_length: int = MAX_FIELD_LENGTH) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text[:max_length]


def clean_sheet_cell(value: object, max_length: int = MAX_FIELD_LENGTH) -> str:
    text = clean_text(value, max_length)
    if text.startswith(SHEET_FORMULA_PREFIXES):
        return "'" + text
    return text


def secret_section(name: str) -> dict:
    try:
        if name not in st.secrets:
            return {}
        return dict(st.secrets[name])
    except Exception:
        return {}


def validate_lead(raw_lead: dict[str, object]) -> tuple[bool, str, dict[str, str]]:
    lead = {
        "Thời gian gửi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Họ tên": clean_sheet_cell(raw_lead.get("name")),
        "Khu vực xây dựng": clean_sheet_cell(raw_lead.get("location")),
        "Diện tích dự kiến": clean_sheet_cell(raw_lead.get("area")),
        "Số tầng dự kiến": clean_sheet_cell(raw_lead.get("floors")),
        "Hạng mục quan tâm": clean_sheet_cell(raw_lead.get("service")),
        "Thời gian triển khai": clean_sheet_cell(raw_lead.get("start_time")),
        "Ngân sách dự kiến": clean_sheet_cell(raw_lead.get("budget"), MAX_BUDGET_LENGTH),
        "Số điện thoại/Zalo": clean_sheet_cell(raw_lead.get("phone"), MAX_PHONE_LENGTH),
    }

    required_headers = [header for header in LEAD_HEADERS if header != "Thời gian gửi"]
    if any(not lead[header] for header in required_headers):
        return False, "missing", lead

    phone = lead["Số điện thoại/Zalo"].lstrip("'")
    if not PHONE_PATTERN.match(phone):
        return False, "phone", lead

    return True, "", lead


def image_url(path: str) -> str:
    if not path:
        return ""
    if path.startswith(("http://", "https://", "data:")):
        return path

    image_path = BASE_DIR / path
    if not image_path.exists():
        return ""

    if path.startswith("static/"):
        static_path = path.removeprefix("static/").replace("\\", "/")
        return f"/app/static/{static_path}"

    return image_path.as_posix()


def bg_style(path: str, fallback: str) -> str:
    url = image_url(path)
    if not url:
        return f"background-image: {fallback};"
    return f"background-image: url('{e(url)}');"


def image_tag(path: str, alt: str) -> str:
    url = image_url(path)
    if not url:
        return ""
    return f'<img src="{e(url)}" alt="{e(alt)}" loading="lazy">'


def youtube_embed_url(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    video_id = ""

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith("/embed/") or parsed.path.startswith("/shorts/"):
            video_id = parsed.path.strip("/").split("/")[1]

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return ""

    return f"https://www.youtube-nocookie.com/embed/{video_id}?rel=0&modestbranding=1&playsinline=1"


def video_tag(url: str, title: str) -> str:
    embed_url = youtube_embed_url(url)
    if not embed_url:
        return ""
    return (
        f'<iframe src="{e(embed_url)}" title="{e(title)}" loading="lazy" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        'allowfullscreen></iframe>'
    )


def append_lead_to_google_sheet(lead: dict[str, str]) -> tuple[bool, str]:
    config = secret_section("google_apps_script")
    if config:
        web_app_url = str(config.get("web_app_url", "")).strip()
        token = str(config.get("token", "")).strip()
        if not web_app_url:
            return False, "Chưa cấu hình Google Apps Script Web App URL."
        if not token:
            return False, "Chưa cấu hình token bảo mật cho Google Apps Script."

        payload = json.dumps({"token": token, "lead": lead}, ensure_ascii=False).encode("utf-8")
        request = Request(
            web_app_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=12) as response:
                body = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            return False, f"Google Apps Script trả lỗi HTTP {exc.code}."
        except URLError as exc:
            return False, f"Không kết nối được Google Apps Script: {exc.reason}"
        except TimeoutError:
            return False, "Google Apps Script phản hồi quá lâu."

        try:
            result = json.loads(body)
        except json.JSONDecodeError:
            return False, "Google Apps Script trả phản hồi không hợp lệ."

        if not result.get("ok"):
            return False, str(result.get("error") or "Google Apps Script không ghi được lead.")
        return True, ""

    sheet_config = secret_section("google_sheet")
    account_info = secret_section("gcp_service_account")
    if not sheet_config or not account_info:
        return False, "Chưa cấu hình Google Apps Script hoặc Google Sheet trong Streamlit secrets."

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return False, "Thiếu thư viện Google Sheet. Hãy cài lại dependencies từ requirements.txt."

    spreadsheet_id = str(sheet_config.get("spreadsheet_id", "")).strip()
    worksheet_name = str(sheet_config.get("worksheet_name", "Leads")).strip() or "Leads"
    if not spreadsheet_id:
        return False, "Chưa cấu hình spreadsheet_id cho Google Sheet."

    if "private_key" in account_info:
        account_info["private_key"] = account_info["private_key"].replace("\\n", "\n")

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(account_info, scopes=scopes)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=len(LEAD_HEADERS))

    if not worksheet.row_values(1):
        worksheet.append_row(LEAD_HEADERS, value_input_option="USER_ENTERED")

    worksheet.append_row([lead.get(header, "") for header in LEAD_HEADERS], value_input_option="USER_ENTERED")
    return True, ""


def tracking_config() -> dict[str, str]:
    config = secret_section("tracking")
    if not config:
        return {}
    return {
        "meta_pixel_id": str(config.get("meta_pixel_id", "")).strip(),
        "ga4_measurement_id": str(config.get("ga4_measurement_id", "")).strip(),
    }


def render_tracking_event(event_name: str, ga4_event_name: str | None = None) -> None:
    config = tracking_config()
    meta_pixel_id = config.get("meta_pixel_id", "")
    ga4_measurement_id = config.get("ga4_measurement_id", "")
    if not meta_pixel_id and not ga4_measurement_id:
        return

    fbq_event = "Lead" if event_name == "Lead" else event_name
    ga_event = ga4_event_name or event_name.lower()
    time_on_page_script = ""
    if event_name == "PageView":
        time_on_page_script = """
        [15, 30, 60, 120].forEach(function(seconds) {
            setTimeout(function() {
                if (typeof fbq === 'function') {
                    fbq('trackCustom', 'TimeOnPage', {
                        seconds: seconds,
                        page: 'xhome_ninh_binh_landing'
                    });
                }
                if (typeof gtag === 'function') {
                    gtag('event', 'time_on_page', {
                        event_category: 'engagement',
                        event_label: 'xhome_ninh_binh_landing',
                        value: seconds
                    });
                }
            }, seconds * 1000);
        });
        """

    meta_script = ""
    if meta_pixel_id:
        meta_script = f"""
        !function(f,b,e,v,n,t,s)
        {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
        if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
        n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];
        s.parentNode.insertBefore(t,s)}}(window, document,'script',
        'https://connect.facebook.net/en_US/fbevents.js');
        fbq('init', '{e(meta_pixel_id)}');
        fbq('track', '{e(fbq_event)}');
        """

    ga4_script = ""
    if ga4_measurement_id:
        ga4_script = f"""
        var gtagScript = document.createElement('script');
        gtagScript.async = true;
        gtagScript.src = 'https://www.googletagmanager.com/gtag/js?id={e(ga4_measurement_id)}';
        document.head.appendChild(gtagScript);
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{e(ga4_measurement_id)}');
        gtag('event', '{e(ga_event)}', {{
            event_category: 'landing_page',
            event_label: 'xhome_ninh_binh'
        }});
        """

    components.html(
        f"""
        <script>
        {meta_script}
        {ga4_script}
        {time_on_page_script}
        </script>
        """,
        height=0,
        width=0,
    )


content = load_content()

st.set_page_config(
    page_title=content["meta"]["page_title"],
    page_icon=content["meta"].get("page_icon", "X"),
    layout="wide",
)

render_tracking_event("PageView", "page_view")


load_css("styles/landing.css")


hero = content["hero"]
features = content["features"]
trust = content["trust_band"]
projects = content["projects"]
process = content["process"]
faq = content["faq"]
form = content["form"]
footer = content.get("footer", {})
logo_html = image_tag(content.get("logo", ""), content["brand"])
footer_addresses = footer.get("addresses") or []
if footer_addresses:
    footer_address_html = "".join(
        f'<span><b>{e(item.get("label", ""))}:</b> {e(item.get("value", ""))}</span>'
        for item in footer_addresses
    )
else:
    footer_address_html = f'<span>{e(footer.get("address", ""))}</span>'
nav_links = "\n".join(
    f'<a class="nav-link" href="#{e(item["target"])}">{e(item["label"])}</a>'
    for item in content.get("nav", [])
)

hero_fallback = (
    "linear-gradient(135deg, rgba(255,255,255,.72), rgba(255,255,255,.18)), "
    "linear-gradient(130deg, #ece3d3 0 28%, #ffffff 28% 50%, #d8dfd5 50% 70%, #8b6f50 70% 100%)"
)
card_fallback = (
    "linear-gradient(145deg, rgba(255,255,255,.72), rgba(255,255,255,.18)), "
    "linear-gradient(135deg, #e4d4bd, #f9f7f2 46%, #b8c6bd 47%, #28313d)"
)
dark_fallback = (
    "linear-gradient(rgba(22,22,23,.82), rgba(22,22,23,.82)), "
    "radial-gradient(circle at 16% 20%, rgba(0,113,227,.32), transparent 30%), "
    "radial-gradient(circle at 82% 74%, rgba(160,106,43,.32), transparent 30%), #161617"
)

feature_cards = "\n".join(
    f"""
    <div class="feature-card">
        <h3>{e(item["title"])}</h3>
        <p>{e(item["body"])}</p>
        <div class="card-visual">{image_tag(item.get("image", ""), item["title"])}</div>
        <div class="media-cta-row"><a class="section-mini-cta" href="#dang-ky">Nhận tư vấn thiết kế</a></div>
    </div>
    """
    for item in features["cards"]
)

stats = "\n".join(
    f"""
    <div class="stat">
        <strong>{e(item["value"])}</strong>
        <span>{e(item["label"])}</span>
    </div>
    """
    for item in trust["stats"]
)

project_cards = "\n".join(
    f"""
    <article class="project-card">
        <div class="project-image">{image_tag(item.get("image", ""), item["title"])}</div>
        <div class="media-cta-row"><a class="section-mini-cta" href="#dang-ky">Nhận tư vấn thiết kế</a></div>
        <div class="project-copy">
            <span>{e(item["type"])}</span>
            <strong>{e(item["title"])}</strong>
            <p>{e(item["body"])}</p>
        </div>
    </article>
    """
    for item in projects["items"]
)

process_items = "\n".join(
    f"""
    <div class="process-item">
        <strong>{e(idx)}. {e(item["title"])}</strong>
        <span>{e(item["body"])}</span>
    </div>
    """
    for idx, item in enumerate(process["items"], start=1)
)

faq_items = "\n".join(
    f"""
    <details class="faq-item">
        <summary>{e(item["question"])}</summary>
        <p>{e(item["answer"])}</p>
    </details>
    """
    for item in faq["items"]
)

st.html(
    f"""
    <nav class="apple-nav">
        <a class="brand-mark" href="#tu-van">
            <span class="brand-logo">{logo_html}</span>
            <span>{e(content["brand"])}</span>
        </a>
        <div class="nav-menu">{nav_links}</div>
    </nav>

    <div class="top-offer">
        {e(content["top_offer"]["text"])}
        <span> {e(content["top_offer"]["highlight"])}</span>
    </div>

    <a class="mobile-sticky-cta" href="#dang-ky">{e(content["mobile_cta"])}</a>

    <section class="hero" id="tu-van">
        <div class="eyebrow">{e(hero["eyebrow"])}</div>
        <h1>{e(hero["headline"])}</h1>
        <p class="hero-subtitle">{e(hero["subtitle"])}</p>
        <div class="hero-actions">
            <a href="#dang-ky">{e(hero["primary_link"])} &gt;</a>
            <a href="#quy-trinh">{e(hero["secondary_link"])} &gt;</a>
        </div>
    </section>
    """
)

if hero.get("video"):
    st.video(hero["video"], autoplay=True, muted=True, loop=True, width="stretch")
    if hero.get("video_caption"):
        st.html(f'<p class="hero-video-caption"><strong>{e(hero["video_caption"])}</strong></p>')
    st.html('<div class="hero-media-cta-row"><a class="section-mini-cta" href="#dang-ky">Nhận tư vấn thiết kế</a></div>')

st.html(
    f"""
    <section class="section" id="giai-phap">
        <div class="section-inner">
            <div class="section-kicker">{e(features["kicker"])}</div>
            <h2 class="section-title">{e(features["title"])}</h2>
            <div class="feature-grid">{feature_cards}</div>
        </div>
    </section>

    <section class="dark-band" id="nang-luc" style="{bg_style(trust.get("background_image", ""), dark_fallback)}">
        <div class="dark-band-overlay">
            <div class="band-copy-panel">
                <h2 class="band-title">{e(trust["title"])}</h2>
                <p class="band-copy">{e(trust["body"])}</p>
            </div>
            <div class="stat-row">{stats}</div>
        </div>
    </section>

    <section class="section" id="du-an">
        <div class="section-inner">
            <div class="section-kicker">{e(projects["kicker"])}</div>
            <h2 class="section-title">{e(projects["title"])}</h2>
            <div class="project-grid">{project_cards}</div>
        </div>
    </section>

    <section class="section" id="quy-trinh">
        <div class="section-inner process">
            <div>
                <div class="section-kicker">{e(process["kicker"])}</div>
                <h2 class="section-title">{e(process["title"])}</h2>
            </div>
            <div class="process-list">{process_items}</div>
        </div>
    </section>

    <section class="section" id="faq">
        <div class="section-inner">
            <div class="section-kicker">{e(faq["kicker"])}</div>
            <h2 class="section-title">{e(faq["title"])}</h2>
            <div class="faq-list">{faq_items}</div>
        </div>
    </section>

    <section class="form-band" id="dang-ky">
        <div class="form-layout">
            <div class="form-copy">
                <h2>{e(form["title"])}</h2>
                <p>{e(form["body"])}</p>
                <div class="form-helper">{e(form.get("helper_text", ""))}</div>
            </div>
            <div>
    """
)


with st.form("xhome_lead_form", clear_on_submit=False):
    name = st.text_input(form["fields"]["name"], max_chars=MAX_FIELD_LENGTH)
    location = st.text_input(form["fields"]["location"], max_chars=MAX_FIELD_LENGTH)
    area = st.text_input(form["fields"]["area"], max_chars=MAX_FIELD_LENGTH)
    floors = st.text_input(form["fields"]["floors"], max_chars=MAX_FIELD_LENGTH)
    service = st.selectbox(form["fields"]["service"], form["service_options"])
    start_time = st.selectbox(form["fields"]["start_time"], form["start_time_options"])
    budget = st.text_input(form["fields"]["budget"], max_chars=MAX_BUDGET_LENGTH)
    phone = st.text_input(form["fields"]["phone"], max_chars=MAX_PHONE_LENGTH)
    submitted = st.form_submit_button(form["submit_label"])


if submitted:
    valid, validation_error, lead = validate_lead(
        {
            "name": name,
            "location": location,
            "area": area,
            "floors": floors,
            "service": service,
            "start_time": start_time,
            "budget": budget,
            "phone": phone,
        }
    )
    if not valid and validation_error == "missing":
        st.warning(form["warning"])
    elif not valid and validation_error == "phone":
        st.warning(form.get("phone_warning", "Anh/chị vui lòng kiểm tra lại số điện thoại/Zalo."))
    else:
        saved, error_message = append_lead_to_google_sheet(lead)
        if saved:
            st.success(form["success"])
            render_tracking_event("Lead", "lead_submit")
        else:
            st.error(error_message)


st.html(
    f"""
            </div>
        </div>
    </section>
    <footer class="site-footer">
        <div class="footer-inner">
            <div class="footer-brand">
                <span class="footer-logo">{logo_html}</span>
            </div>
            <div class="footer-item">
                <strong>Văn phòng công ty XHOME Ninh Bình</strong>
                <span>{e(footer.get("company", content["brand"]))}</span>
            </div>
            <div class="footer-item">
                <strong>Địa chỉ</strong>
                <span class="footer-addresses">{footer_address_html}</span>
            </div>
            <div class="footer-item">
                <strong>Liên hệ</strong>
                <span class="footer-lines">
                    <span><b>Hotline:</b> {e(footer.get("hotline", ""))}</span>
                    <span><b>Email:</b> {e(footer.get("email", ""))}</span>
                    <span><b>Mã số thuế:</b> {e(footer.get("tax_code", ""))}</span>
                </span>
            </div>
        </div>
    </footer>
    """
)
