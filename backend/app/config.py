import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Resolve to the project root (parent of /backend) so the desktop app
# always stores data next to the pack, even when launched from Finder/Explorer.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://pdfuser:pdfsecret@localhost:5432/ilovepdf_db"
    FALLBACK_SQLITE_URL: str = f"sqlite+aiosqlite:///{(DATA_DIR / 'ilovepdf.db').as_posix()}"
    STORAGE_DIR: str = str(DATA_DIR / "storage")
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    SECRET_KEY: str = "dev-secret-key-change-in-production-123456789"
    LOCAL_MASTER_PASSWORD: str = "admin123"  # Local personal master password
    FRONTEND_URL: str = "http://127.0.0.1:3000"
    TESSERACT_CMD: str = "tesseract"
    LIBREOFFICE_CMD: str = "soffice"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Force all data paths to be absolute against the pack root, no matter what
# the .env file says. This lets the desktop app work when launched from any
# working directory (Finder, Explorer, .app bundle, .vbs wrapper, etc.).
if not os.path.isabs(settings.STORAGE_DIR):
    settings.STORAGE_DIR = str((PROJECT_ROOT / settings.STORAGE_DIR).resolve())

# Always pin SQLite to the pack's data/ folder (absolute URI).
settings.FALLBACK_SQLITE_URL = f"sqlite+aiosqlite:///{(DATA_DIR / 'ilovepdf.db').as_posix()}"

# Desktop pack always listens on localhost.
settings.APP_HOST = "127.0.0.1"
settings.FRONTEND_URL = "http://127.0.0.1:3000"

os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "originals"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "outputs"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "previews"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "backups"), exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
