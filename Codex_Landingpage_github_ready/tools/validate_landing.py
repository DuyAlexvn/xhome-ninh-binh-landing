from __future__ import annotations

import json
from pathlib import Path
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = ROOT / "content" / "content.json"
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"

REQUIRED_FORM_FIELDS = [
    "name",
    "location",
    "area",
    "floors",
    "service",
    "start_time",
    "budget",
    "phone",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def load_content() -> dict:
    if not CONTENT_PATH.exists():
        fail(f"Missing {CONTENT_PATH.relative_to(ROOT)}")
    try:
        return json.loads(CONTENT_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid content JSON: {exc}")


def iter_image_paths(content: dict):
    logo = content.get("logo")
    if logo:
        yield "logo", logo

    hero = content.get("hero", {})
    if hero.get("image"):
        yield "hero.image", hero["image"]

    trust = content.get("trust_band", {})
    if trust.get("background_image"):
        yield "trust_band.background_image", trust["background_image"]

    for index, item in enumerate(content.get("features", {}).get("cards", []), start=1):
        if item.get("image"):
            yield f"features.cards[{index}].image", item["image"]

    for index, item in enumerate(content.get("projects", {}).get("items", []), start=1):
        if item.get("image"):
            yield f"projects.items[{index}].image", item["image"]


def validate_images(content: dict) -> None:
    for label, value in iter_image_paths(content):
        path = str(value).strip()
        if path.startswith(("http://", "https://", "data:")):
            continue
        if ":\\" in path or ":/" in path:
            fail(f"{label} uses local absolute path: {path}")
        if not (ROOT / path).exists():
            fail(f"{label} points to missing file: {path}")
    ok("Image references are deployable")


def validate_form(content: dict) -> None:
    form = content.get("form", {})
    fields = form.get("fields", {})
    missing = [field for field in REQUIRED_FORM_FIELDS if field not in fields]
    if missing:
        fail(f"Missing form fields in content.json: {', '.join(missing)}")
    ok("Required form fields are present")


def validate_footer(content: dict) -> None:
    footer = content.get("footer", {})
    required = ["company", "hotline", "email", "tax_code"]
    missing = [field for field in required if not str(footer.get(field, "")).strip()]
    if missing:
        warn(f"Footer is missing recommended ad-trust fields: {', '.join(missing)}")
    if not footer.get("addresses") and not footer.get("address"):
        warn("Footer has no address")
    else:
        ok("Footer trust fields are present")


def validate_secrets() -> None:
    if not SECRETS_PATH.exists():
        warn("No local .streamlit/secrets.toml found. This is OK for GitHub, but deploy needs secrets.")
        return

    secrets = tomllib.loads(SECRETS_PATH.read_text(encoding="utf-8"))
    apps_script = secrets.get("google_apps_script", {})
    web_app_url = str(apps_script.get("web_app_url", "")).strip()
    token = str(apps_script.get("token", "")).strip()

    if web_app_url:
        if not web_app_url.startswith("https://script.google.com/macros/s/"):
            fail("google_apps_script.web_app_url does not look like an Apps Script Web App URL")
        if not token or "CHANGE_THIS" in token:
            fail("google_apps_script.token is empty or still a placeholder")
        ok("Apps Script secrets are configured")
        return

    service_account = secrets.get("gcp_service_account", {})
    client_email = str(service_account.get("client_email", "")).strip()
    if client_email and "PASTE_" not in client_email:
        ok("Service account secrets are configured")
        return

    warn("No usable Google lead destination configured in local secrets")


def main() -> int:
    content = load_content()
    validate_images(content)
    validate_form(content)
    validate_footer(content)
    validate_secrets()
    ok("Landing validation finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
