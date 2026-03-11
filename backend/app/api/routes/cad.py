"""CAD generation and export API."""
import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models import Product, CadModel
from app.models.product import ProductStatus
from app.services.cad_service import suggest_cad_from_product
from app.schemas.cad import CadCreate, CadModelResponse, CadExportResult
from app.services.cad_service import (
    generate_scad_code,
    save_scad_file,
    export_stl as run_export_stl,
    check_openscad_available,
    MODEL_TYPES,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/openscad-available")
def openscad_available() -> dict:
    """Check if OpenSCAD CLI is available for STL export."""
    available, message = check_openscad_available()
    return {"available": available, "message": message or None}


@router.get("/model-types", response_model=list[str])
def list_model_types() -> list[str]:
    """List available CAD template types."""
    return MODEL_TYPES


@router.get("/{product_id}/cad", response_model=list[CadModelResponse])
async def list_cad_models(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[CadModelResponse]:
    """List all CAD models for a product."""
    result = await db.execute(
        select(CadModel).where(CadModel.product_id == product_id).order_by(CadModel.version.desc())
    )
    models = result.scalars().all()
    return [
        CadModelResponse(
            id=m.id,
            product_id=m.product_id,
            version=m.version,
            model_type=m.model_type,
            parameters_json=m.parameters_json,
            scad_code=m.scad_code,
            scad_file_path=m.scad_file_path,
            stl_file_path=m.stl_file_path,
            generation_method=m.generation_method,
            created_at=m.created_at,
        )
        for m in models
    ]


@router.post("/{product_id}/cad", response_model=CadModelResponse, status_code=201)
async def create_cad_model(
    product_id: int,
    payload: CadCreate,
    db: AsyncSession = Depends(get_db),
) -> CadModelResponse:
    """Generate and save a new CAD model. Claude designs the shape from product name, category, and research (Etsy best-seller style). No template fallback."""
    result = await db.execute(
        select(Product).where(Product.id == product_id).options(selectinload(Product.research_data))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found. It may have been deleted or the database was reset (e.g. after a redeploy). Refresh the page and select a product again.",
        )

    notes = None
    if product.research_data:
        r = product.research_data[0]
        parts = [r.notes or "", f"Price: {r.listed_price}" if r.listed_price else "", f"Competitors: {r.competitor_count}" if r.competitor_count is not None else ""]
        notes = " ".join(p for p in parts if p).strip() or None
    suggestion = suggest_cad_from_product(product.name, product.category, notes)
    if not suggestion:
        raise HTTPException(
            status_code=503,
            detail="CAD generation requires Claude. Set FORGEFLOW_CAD_LLM_API_KEY (Anthropic) and FORGEFLOW_CAD_LLM_PROVIDER=anthropic in your environment.",
        )
    model_type, parameters = suggestion

    if model_type not in MODEL_TYPES:
        raise HTTPException(
            status_code=500,
            detail=f"Claude returned invalid model_type. Choose from: {MODEL_TYPES}",
        )
    try:
        code = generate_scad_code(model_type, parameters)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Next version number
    count_result = await db.execute(
        select(CadModel).where(CadModel.product_id == product_id)
    )
    existing = count_result.scalars().all()
    version = len(existing) + 1

    scad_path = save_scad_file(product_id, version, code, product.slug)
    parameters_json = json.dumps(parameters)

    cad = CadModel(
        product_id=product_id,
        version=version,
        model_type=model_type,
        parameters_json=parameters_json,
        scad_code=code,
        scad_file_path=str(scad_path),
        stl_file_path=None,
        generation_method="llm",
    )
    db.add(cad)
    product.status = ProductStatus.CAD_GENERATED
    await db.flush()
    await db.refresh(cad)

    return CadModelResponse(
        id=cad.id,
        product_id=cad.product_id,
        version=cad.version,
        model_type=cad.model_type,
        parameters_json=cad.parameters_json,
        scad_code=cad.scad_code,
        scad_file_path=cad.scad_file_path,
        stl_file_path=cad.stl_file_path,
        generation_method=cad.generation_method,
        created_at=cad.created_at,
    )


@router.get("/{product_id}/cad/{cad_id}", response_model=CadModelResponse)
async def get_cad_model(
    product_id: int,
    cad_id: int,
    db: AsyncSession = Depends(get_db),
) -> CadModelResponse:
    """Get a single CAD model."""
    result = await db.execute(
        select(CadModel).where(CadModel.id == cad_id, CadModel.product_id == product_id)
    )
    cad = result.scalar_one_or_none()
    if not cad:
        raise HTTPException(status_code=404, detail="CAD model not found")
    return CadModelResponse(
        id=cad.id,
        product_id=cad.product_id,
        version=cad.version,
        model_type=cad.model_type,
        parameters_json=cad.parameters_json,
        scad_code=cad.scad_code,
        scad_file_path=cad.scad_file_path,
        stl_file_path=cad.stl_file_path,
        generation_method=cad.generation_method,
        created_at=cad.created_at,
    )


@router.post("/{product_id}/cad/{cad_id}/export-stl", response_model=CadExportResult)
async def export_cad_to_stl(
    product_id: int,
    cad_id: int,
    db: AsyncSession = Depends(get_db),
) -> CadExportResult:
    """Run OpenSCAD to export this CAD model to STL. Updates stl_file_path on success."""
    result = await db.execute(
        select(CadModel).where(CadModel.id == cad_id, CadModel.product_id == product_id)
    )
    cad = result.scalar_one_or_none()
    if not cad:
        raise HTTPException(status_code=404, detail="CAD model not found")
    if not cad.scad_file_path or not Path(cad.scad_file_path).exists():
        return CadExportResult(
            success=False,
            message="SCAD file not found on disk. Re-generate the CAD model.",
        )

    stl_name = Path(cad.scad_file_path).stem + ".stl"
    stl_path = settings.stl_dir / stl_name
    success, message = run_export_stl(Path(cad.scad_file_path), stl_path)

    if success:
        cad.stl_file_path = str(stl_path)
        await db.flush()
        return CadExportResult(
            success=True,
            message="STL exported successfully.",
            stl_file_path=cad.stl_file_path,
        )
    return CadExportResult(success=False, message=message)


@router.get("/{product_id}/cad/{cad_id}/stl")
async def download_stl(
    product_id: int,
    cad_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Stream the exported STL file for download. Use in 3D printer software (slicer)."""
    try:
        result = await db.execute(
            select(CadModel).where(CadModel.id == cad_id, CadModel.product_id == product_id)
        )
        cad = result.scalar_one_or_none()
        if not cad:
            raise HTTPException(status_code=404, detail="CAD model not found")
        if not cad.stl_file_path:
            raise HTTPException(
                status_code=404,
                detail="STL not exported yet. Click 'Export STL' first.",
            )
        # Resolve path: stored path may be relative or absolute (e.g. in Docker)
        stored = Path(cad.stl_file_path)
        stl_path = settings.stl_dir / stored.name if not stored.is_absolute() else stored
        if not stl_path.exists():
            stl_path = stored
        if not stl_path.exists():
            raise HTTPException(
                status_code=404,
                detail="STL file not found on server (e.g. after redeploy). Re-export STL.",
            )
        # FileResponse needs an absolute path so streaming works (e.g. on Railway/Docker)
        stl_path = stl_path.resolve()
        # Suggest a clean filename for download (product slug + version)
        product_result = await db.execute(select(Product).where(Product.id == product_id))
        product = product_result.scalar_one_or_none()
        slug = (product.slug if product else None) or f"product-{product_id}"
        download_name = f"{slug}_v{cad.version}.stl"
        return FileResponse(
            path=str(stl_path),
            filename=download_name,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("STL download failed for product_id=%s cad_id=%s", product_id, cad_id)
        raise HTTPException(
            status_code=500,
            detail=f"STL download failed: {str(e)}. Re-export STL and try again.",
        ) from e
