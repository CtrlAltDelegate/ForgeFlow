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

    # Database: either set DATABASE_URL (no FORGEFLOW_ prefix, picked up by get_database_url()) or
    # set FORGEFLOW_PG_HOST/PORT/USER/PASSWORD/DATABASE so the URL is built from current credentials.
    # FORGEFLOW_DATABASE_URL is a last-resort override (e.g. for local dev).
    database_url: str = _DEFAULT_SQLITE_URL
    pg_host: str = ""
    pg_port: str = ""
    pg_user: str = ""
    pg_password: str = ""
    pg_database: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: str | None) -> str:
        # This validator runs when FORGEFLOW_DATABASE_URL is explicitly set.
        # When it is absent, pydantic uses the default _DEFAULT_SQLITE_URL without calling this;
        # the DATABASE_URL / PG_* fallback is handled entirely by get_database_url() at call time.
        if v is None or (isinstance(v, str) and not (v or "").strip()):
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
        """Return the URL to use: DATABASE_URL (if set) else built from PG_* else database_url.

        Priority (highest first):
        1. DATABASE_URL env var -- Railway/Render inject this when a Postgres service is linked.
        2. PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE (or FORGEFLOW_PG_* equivalents).
        3. FORGEFLOW_DATABASE_URL (this Settings field) -- last resort / local override.
        """
        # 1. Prefer platform-injected DATABASE_URL (e.g. set via Railway service variable reference)
        env_url = os.environ.get("DATABASE_URL", "").strip()
        if env_url and "postgres" in env_url.lower() and "${{" not in env_url:
            return self._normalize_url(env_url)

        # 2. Build from individual PG vars -- Railway also injects these automatically
        host = (self.pg_host or "").strip() or os.environ.get("PGHOST", "").strip()
        port = (self.pg_port or "").strip() or os.environ.get("PGPORT", "").strip()
        user = (self.pg_user or "").strip() or os.environ.get("PGUSER", "").strip()
        password = (self.pg_password or "").strip() or os.environ.get("PGPASSWORD", "").strip()
        database = (self.pg_database or "").strip() or os.environ.get("PGDATABASE", "").strip()
        if host and port and user and password and database:
            # Guard against any PG var that somehow contains an unresolved reference
            if any("${{" in v for v in (host, port, user, password, database)):
                return self.database_url
            user_enc = quote_plus(user)
            password_enc = quote_plus(password)
            return f"postgresql+asyncpg://{user_enc}:{password_enc}@{host}:{port}/{database}"

        # 3. Fall back to FORGEFLOW_DATABASE_URL (or the SQLite default if that wasn't set either)
        return self.database_url

    def get_sqlite_url(self) -> str:
        """Return the default SQLite URL (for fallback when Postgres fails)."""
        return _DEFAULT_SQLITE_URL

    # Paths (relative to project root or absolute)
    data_dir: Path = Path("./data")
    scad_dir: Path = Path("./data/scad")
    stl_dir: Path = Path("./data/stl")
    imports_dir: Path = Path("./data/imports")
    intake_images_dir: Path = Path("./data/intake_images")

    # External tools
    openscad_path: str = "openscad"
    slicer_path: str = ""

    # LLM / AI (optional). If set, used for listing/review and CAD generation.
    # Listing/review: gpt-4o-mini (OpenAI). CAD: claude-3-5-sonnet (Anthropic).
    listing_llm_api_key: str = ""
    listing_llm_model: str = "gpt-4o-mini"
    listing_llm_provider: str = "openai"
    cad_llm_api_key: str = ""
    cad_llm_model: str = "claude-sonnet-4-6"  # was claude-3-5-sonnet-20241022 (deprecated, 404)
    cad_llm_provider: str = "anthropic"

    # Intake pipeline AI models (share cad_llm_api_key for Anthropic access)
    intake_vision_model: str = "claude-sonnet-4-6"  # vision + brief assembly (was claude-3-5-sonnet-20241022)
    intake_text_model: str = "claude-haiku-4-5-20251001"      # text extraction (fast/cheap)

    # Default manufacturing assumptions
    default_material_cost_per_gram: float = 0.02
    default_platform_fee_percent: float = 6.5
    default_shipping_estimate: float = 4.0

    class Config:
        env_file = ".env"
        env_prefix = "FORGEFLOW_"
        extra = "ignore"


settings = Settings()
