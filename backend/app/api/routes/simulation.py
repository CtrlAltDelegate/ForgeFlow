"""Manufacturing simulation API."""
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.models import Product, CadModel, ManufacturingSimulation
from app.models.product import ProductStatus
from app.schemas.simulation import SimulationCreate, SimulationResponse, SimulationResultWithWarnings
from app.services.simulation_service import run_simulation, SimulationInputs

router = APIRouter()


@router.get("/{product_id}/simulations", response_model=list[SimulationResponse])
async def list_simulations(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[SimulationResponse]:
    """List manufacturing simulations for a product."""
    result = await db.execute(
        select(ManufacturingSimulation)
        .where(ManufacturingSimulation.product_id == product_id)
        .order_by(ManufacturingSimulation.simulated_at.desc())
    )
    sims = result.scalars().all()
    return [
        SimulationResponse(
            id=s.id,
            product_id=s.product_id,
            cad_model_id=s.cad_model_id,
            material_type=s.material_type,
            layer_height=s.layer_height,
            infill=s.infill,
            nozzle_size=s.nozzle_size,
            estimated_print_time_minutes=s.estimated_print_time_minutes,
            estimated_material_grams=s.estimated_material_grams,
            estimated_filament_cost=s.estimated_filament_cost,
            supports_required=s.supports_required,
            recommended_orientation=s.recommended_orientation,
            difficulty_score=s.difficulty_score,
            notes=s.notes,
            simulated_at=s.simulated_at,
        )
        for s in sims
    ]


@router.post("/{product_id}/simulations", response_model=SimulationResultWithWarnings, status_code=201)
async def create_simulation(
    product_id: int,
    payload: SimulationCreate,
    db: AsyncSession = Depends(get_db),
) -> SimulationResultWithWarnings:
    """Run heuristic manufacturing simulation and save result."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cad_model_type: str | None = None
    cad_parameters_json: str | None = None
    if payload.cad_model_id:
        cad_result = await db.execute(
            select(CadModel).where(
                CadModel.id == payload.cad_model_id,
                CadModel.product_id == product_id,
            )
        )
        cad = cad_result.scalar_one_or_none()
        if cad:
            cad_model_type = cad.model_type
            cad_parameters_json = cad.parameters_json

    inputs = SimulationInputs(
        material_type=payload.material_type,
        layer_height=payload.layer_height,
        infill=payload.infill,
        nozzle_size=payload.nozzle_size,
        cad_model_type=cad_model_type,
        cad_parameters_json=cad_parameters_json,
    )
    sim_result = run_simulation(inputs)

    sim = ManufacturingSimulation(
        product_id=product_id,
        cad_model_id=payload.cad_model_id,
        material_type=payload.material_type,
        layer_height=payload.layer_height,
        infill=payload.infill,
        nozzle_size=payload.nozzle_size,
        estimated_print_time_minutes=sim_result.estimated_print_time_minutes,
        estimated_material_grams=sim_result.estimated_material_grams,
        estimated_filament_cost=sim_result.estimated_filament_cost,
        supports_required=sim_result.supports_required,
        recommended_orientation=sim_result.recommended_orientation,
        difficulty_score=sim_result.difficulty_score,
        notes=sim_result.notes,
    )
    db.add(sim)
    product.status = ProductStatus.MANUFACTURING_SIMULATED
    await db.flush()
    await db.refresh(sim)

    return SimulationResultWithWarnings(
        simulation=SimulationResponse(
            id=sim.id,
            product_id=sim.product_id,
            cad_model_id=sim.cad_model_id,
            material_type=sim.material_type,
            layer_height=sim.layer_height,
            infill=sim.infill,
            nozzle_size=sim.nozzle_size,
            estimated_print_time_minutes=sim.estimated_print_time_minutes,
            estimated_material_grams=sim.estimated_material_grams,
            estimated_filament_cost=sim.estimated_filament_cost,
            supports_required=sim.supports_required,
            recommended_orientation=sim.recommended_orientation,
            difficulty_score=sim.difficulty_score,
            notes=sim.notes,
            simulated_at=sim.simulated_at,
        ),
        warnings=sim_result.warnings,
    )


@router.get("/{product_id}/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    product_id: int,
    simulation_id: int,
    db: AsyncSession = Depends(get_db),
) -> SimulationResponse:
    """Get a single simulation."""
    result = await db.execute(
        select(ManufacturingSimulation).where(
            ManufacturingSimulation.id == simulation_id,
            ManufacturingSimulation.product_id == product_id,
        )
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return SimulationResponse(
        id=s.id,
        product_id=s.product_id,
        cad_model_id=s.cad_model_id,
        material_type=s.material_type,
        layer_height=s.layer_height,
        infill=s.infill,
        nozzle_size=s.nozzle_size,
        estimated_print_time_minutes=s.estimated_print_time_minutes,
        estimated_material_grams=s.estimated_material_grams,
        estimated_filament_cost=s.estimated_filament_cost,
        supports_required=s.supports_required,
        recommended_orientation=s.recommended_orientation,
        difficulty_score=s.difficulty_score,
        notes=s.notes,
        simulated_at=s.simulated_at,
    )
