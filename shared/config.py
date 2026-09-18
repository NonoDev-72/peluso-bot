import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _split_ids(raw: str) -> set[int]:
    return {int(v) for v in raw.split(",") if v.strip()}


@dataclass(frozen=True)
class Settings:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    discord_client_id: str = os.getenv("DISCORD_CLIENT_ID", "")
    discord_client_secret: str = os.getenv("DISCORD_CLIENT_SECRET", "")
    discord_redirect_uri: str = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/callback")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./peluso.db")
    uploads_dir: str = os.getenv("UPLOADS_DIR", "/data/uploads")
    web_secret_key: str = os.getenv("WEB_SECRET_KEY", "change-me")
    web_base_path: str = os.getenv("WEB_BASE_PATH", "").rstrip("/")
    bot_owner_ids: set[int] = field(default_factory=lambda: _split_ids(os.getenv("BOT_OWNER_IDS", "")))


settings = Settings()
