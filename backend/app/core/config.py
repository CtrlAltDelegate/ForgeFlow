"""Application configuration."""
import os
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Resolve backend directory so DB path is always the same regardless of CWD
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_DB_PATH = _BACKEND_DIR / "forgeflow.db"
_DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH.resolve().as_posix()}"


class Settings(BaseSettings):
    """ForgeFlow application settings."""

    app_name: str = "ForgeFlow"
    debug: bool = False

    # CORS: comma-separated origins (e.g. https://yoursite.netlify.app)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://forgeflowdashboard.netlify.app"

    # Database: either set DATABASE_URL or (on Railway) set PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE
    # so the URL is built from current credentials and password auth works.
    database_url: str = _DEFAULT_SQLITE_URL
    pg_host: str = ""
    pg_port: str = ""
    pg_user: str = ""
    pg_password: str = ""
    pg_database: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: str | None) -> str:
        # Use platform-injected DATABASE_URL (e.g. Railway, Render) when FORGEFLOW_DATABASE_URL is not set
        if v is None or (isinstance(v, str) and not (v or "").strip()):
            env_url = os.environ.get("DATABASE_URL")
            if env_url and isinstance(env_url, str) and "postgres" in env_url.lower():
                v = env_url
        if v is None or not isinstance(v, str):
            return _DEFAULT_SQLITE_URL
        raw = v.strip()
        if not raw or "${{" in raw or (raw.startswith("$") and "://" not in raw):
            return _DEFAULT_SQLITE_URL
        if raw.startswith("postgres://") and not raw.startswith("postgresql+"):
            return "postgresql+asyncpg://" + raw[11:]
        if raw.startswith("postgresql://") and not raw.startswith("postgresql+asyncpg://"):
            return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
        return raw

    @classmethod
    def _normalize_url(cls, url: str) -> str:
        """Normalize a postgres URL to postgresql+asyncpg:// form."""
        if not url or "postgres" not in url.lower():
            return url
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[11:]
        if url.startswith("postgresql://") and "postgresql+asyncpg://" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    def get_database_url(self) -> str:
        """Return the URL to use: DATABASE_URL (if set) else built from PG_* else database_url."""
        # Prefer platform-injected DATABASE_URL (Railway/Render link Postgres and set this on the service)
        env_url = os.environ.get("DATABASE_URL")
        if env_url and isinstance(env_url, str) and "postgres" in env_url.lower() and "${{" not in env_url:
            return self._normalize_url(env_url.strip())
        # Else build from FORGEFLOW_PG_* or platform PG* (PGHOST, PGPASSWORD, etc.)
        host = (self.pg_host or "").strip() or os.environ.get("PGHOST", "")
        port = (self.pg_port or "").strip() or os.environ.get("PGPORT", "")
        user = (self.pg_user or "").strip() or os.environ.get("PGUSER", "")
        password = (self.pg_password or "") or os.environ.get("PGPASSWORD", "")
        database = (self.pg_database or "").strip() or os.environ.get("PGDATABASE", "")
        parts = [host, port, user, password, database]
        if all(parts) and "${{" not in (password or ""):
            user_enc = quote_plus(user)
            password_enc = quote_plus(password)
            return f"postgresql+asyncpg://{user_enc}:{password_enc}@{host}:{port}/{database}"
        return self.database_url

    def get_sqlite_url(self) -> str:
        """Return the default SQLite URL (for fallback when Postgres fails)."""
        return _DEFAULT_SQLITE_URL

    # Paths (relative to project root or absolute)
    data_dir: Path = Path("./data")
    scad_dir: Path = Path("./data/scad")
    stl_dir: Path = Path("./data/stl")
    imports_dir: Path = Path("./data/imports")

    # External tools
    openscad_path: str = "openscad"
    slicer_path: str = ""

    # LLM / AI (optional). If set, used for listing/review and CAD generation.
    # Listing/review: gpt-4o-mini (OpenAI). CAD: claude-3-5-sonnet (Anthropic).
    listing_llm_api_key: str = ""
    listing_llm_model: str = "gpt-4o-mini"
    listing_llm_provider: str = "openai"
    cad_llm_api_key: str = ""
    cad_llm_model: str = "claude-3-5-sonnet-20241022"
    cad_llm_provider: str = "anthropic"

    # Default manufacturing assumptions
    default_material_cost_per_gram: float = 0.02
    default_platform_fee_percent: float = 6.5
    default_shipping_estimate: float = 4.0

    class Config:
        env_file = ".env"
        env_prefix = "FORGEFLOW_"
        extra = "ignore"


settings = Settings()
