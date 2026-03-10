"""Application configuration."""
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Resolve backend directory so DB path is always the same regardless of CWD
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_DB_PATH = _BACKEND_DIR / "forgeflow.db"


class Settings(BaseSettings):
    """ForgeFlow application settings."""

    app_name: str = "ForgeFlow"
    debug: bool = False

    # CORS: comma-separated origins (e.g. https://yoursite.netlify.app)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://forgeflowdashboard.netlify.app,https://forgeflow-dashboard.netlify.app"

    # Database: default is absolute path in backend folder so data persists across restarts.
    # For Postgres (e.g. Railway), set FORGEFLOW_DATABASE_URL to the Postgres URL (not a variable reference).
    database_url: str = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH.resolve().as_posix()}"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: str | None) -> str:
        default = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH.resolve().as_posix()}"
        if v is None or not isinstance(v, str):
            return default
        raw = v.strip()
        # Unresolved Railway ref (e.g. ${{Postgres.DATABASE_URL}}) or empty -> use SQLite so app starts
        if not raw or "${{" in raw or (raw.startswith("$") and "://" not in raw):
            return default
        # Use asyncpg for Postgres
        if raw.startswith("postgres://") and not raw.startswith("postgresql+"):
            return "postgresql+asyncpg://" + raw[11:]
        if raw.startswith("postgresql://") and not raw.startswith("postgresql+asyncpg://"):
            return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
        return raw

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
