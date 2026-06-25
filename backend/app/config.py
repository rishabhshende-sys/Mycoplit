from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
STORAGE_DIR = APP_DIR / "storage"
SCREENSHOT_DIR = STORAGE_DIR / "screenshots"
UPLOAD_DIR = STORAGE_DIR / "uploads"
CLEANED_DIR = STORAGE_DIR / "cleaned"
REPORT_DIR = STORAGE_DIR / "reports"
DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'mycoplit.db').as_posix()}"

APP_NAME = "Mycoplit Visual AI Command Center"
DEFAULT_MODE = "read-only"
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def ensure_storage() -> None:
    for path in [SCREENSHOT_DIR, UPLOAD_DIR, CLEANED_DIR, REPORT_DIR, STORAGE_DIR / "logs"]:
        path.mkdir(parents=True, exist_ok=True)
