"""CAD model schemas."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class CadParameters(BaseModel):
    """Flexible parameters for template-based CAD (keys depend on model_type)."""
    width: float | None = None
    height: float | None = None
    depth: float | None = None
    thickness: float | None = None
    wall_thickness: float | None = None
    hole_diameter: float | None = None
    inner_diameter: float | None = None
    outer_diameter: float | None = None
    inner_radius: float | None = None
    length: float | None = None
    channel_radius: float | None = None

    class Config:
        extra = "allow"


class CadCreate(BaseModel):
    """Body for creating a CAD model. ForgeFlow is Claude-only: design is always from Claude (product + category)."""
    model_type: str | None = None  # ignored; Claude chooses
    parameters: dict[str, Any] | None = None  # ignored; Claude chooses


class CadModelResponse(BaseModel):
    id: int
    product_id: int
    version: int
    model_type: str
    parameters_json: str | None
    scad_code: str | None
    scad_file_path: str | None
    stl_file_path: str | None
    generation_method: str
    created_at: datetime

    class Config:
        from_attributes = True


class CadExportResult(BaseModel):
    success: bool
    message: str
    stl_file_path: str | None = None
