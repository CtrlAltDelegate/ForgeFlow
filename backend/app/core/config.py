"""Application configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ForgeFlow application settings."""

    app_name: str = "ForgeFlow"
    debug: bool = False

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

    # Default manufacturing assumptions
    default_material_cost_per_gram: float = 0.02
    default_platform_fee_percent: float = 6.5
    default_shipping_estimate: float = 4.0

    class Config:
        env_file = ".env"
        env_prefix = "FORGEFLOW_"
        extra = "ignore"


settings = Settings()
