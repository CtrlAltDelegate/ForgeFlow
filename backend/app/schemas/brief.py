"""ProductBrief Pydantic schema — canonical brief format for the intake pipeline.

This schema defines the structure of approved_brief_json stored in ProductIntake
and copied into CadModel.parameters_json on approval. It matches the field
reference in Section 4.2 of the Intake Pipeline Design Spec v1.0.

extra="allow" is set on ProductBrief so that product-specific sub-objects
(e.g. slot_geometry, base_treatment) survive validation without being stripped.
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DimensionsMM(BaseModel):
    """Length / width / height plus optional product-specific sub-dimensions."""

    length: float
    width: float
    height: float

    # Allow extra keys for product-specific critical sub-dimensions
    # (e.g. slot_diameter_mm, shelf_depth_mm)
    model_config = ConfigDict(extra="allow")


class ParametricVariable(BaseModel):
    """One axis of SKU expansion for a product."""

    name: str
    controls: str  # what this variable drives
    min: float
    max: float
    default: float | None = None

    model_config = ConfigDict(extra="allow")


class ProductBrief(BaseModel):
    """
    Full product brief — the single source of truth for CAD generation.

    Required fields mirror the gate conditions in Section 3.3.3 of the spec.
    Field names match product_briefs.json where they overlap.
    """

    # --- Identifiers ---
    product_id: str
    product_name: str
    product_type: str
    schema_version: str = "1.0"

    # --- Core description (all gate-required) ---
    primary_use_case: str
    primary_geometry: str
    dominant_features: list[str] = Field(min_length=3)
    approximate_dimensions_mm: DimensionsMM
    edge_treatment: str
    aesthetic: str
    print_orientation: str
    support_required: bool
    avoid: list[str] = Field(min_length=3)
    resemblance_goal: str

    # --- Parametric / manufacturing ---
    parametric_variables: list[ParametricVariable] = Field(min_length=1)
    openscad_prompt: str = Field(min_length=150)
    material: str  # PLA | PETG | TPU | ABS
    estimated_print_time_hrs: float
    estimated_filament_g: float

    # --- Recommended (improve CAD quality, do not block) ---
    sku_expansion_strategy: str | None = None
    commercial_differentiators: str | None = None

    # --- Optional market data ---
    forgescore_demand: int | None = None
    price_range_usd: list[float] | None = None
    phase: str | None = None

    # Allow product-specific extra keys (e.g. slot_geometry, base_treatment)
    # so fully-detailed briefs aren't rejected by the schema validator
    model_config = ConfigDict(extra="allow")

    @field_validator("material")
    @classmethod
    def validate_material(cls, v: str) -> str:
        allowed = {"PLA", "PETG", "TPU", "ABS"}
        if v.upper() not in allowed:
            raise ValueError(f"material must be one of {allowed}, got '{v}'")
        return v.upper()
