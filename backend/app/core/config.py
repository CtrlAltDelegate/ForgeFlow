"""Application configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ForgeFlow application settings."""

    app_name: str = "ForgeFlow"
    debug: bool = False

    # CORS: comma-separated origins (e.g. https://yoursite.netlify.app)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://forgeflowdashboard.netlify.app"

    # Database
    database_url: str = "sqlite+aiosqlite:///./forgeflow.db"

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
