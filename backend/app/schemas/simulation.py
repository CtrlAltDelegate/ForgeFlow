"""Manufacturing simulation schemas."""
from datetime import datetime
from pydantic import BaseModel


class SimulationCreate(BaseModel):
    cad_model_id: int | None = None
    material_type: str = "PLA"
    layer_height: float = 0.2
    infill: float = 20.0
    nozzle_size: float = 0.4


class SimulationResponse(BaseModel):
    id: int
    product_id: int
    cad_model_id: int | None
    material_type: str
    layer_height: float
    infill: float
    nozzle_size: float
    estimated_print_time_minutes: float | None
    estimated_material_grams: float | None
    estimated_filament_cost: float | None
    supports_required: bool
    recommended_orientation: str | None
    difficulty_score: float | None
    notes: str | None
    simulated_at: datetime

    class Config:
        from_attributes = True


class SimulationResultWithWarnings(BaseModel):
    simulation: SimulationResponse
    warnings: list[str] = []
