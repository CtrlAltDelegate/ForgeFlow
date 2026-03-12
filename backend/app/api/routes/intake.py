"""Phase C — API routes for the product intake pipeline.

Endpoints:
  POST   /api/intake/submit               — submit a new intake (etsy_url / erank_paste / manual)
  GET    /api/intake                      — list all intakes (paginated)
  GET    /api/intake/{id}                 — get single intake with images
  POST   /api/intake/{id}/approve         — approve a draft brief, create Product + CadModel
  POST   /api/intake/{id}/reject          — reject an intake
  POST   /api/intake/{id}/re-enrich       — re-run Stage 2 enrichment as BackgroundTask
  PATCH  /api/intake/{id}/brief           — patch a single field in draft_brief_json
  POST   /api/intake/{id}/regenerate-prompt — regenerate openscad_prompt field
"""
import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.cad_model import CadModel
from app.models.intake import IntakeImage, IntakeStatus, ProductIntake
from app.models.product import Product, ProductStatus, slugify
from app.schemas.intake import (
    BriefFieldUpdate,
    IntakeApproveRequest,
    IntakeApproveResponse,
    IntakeListItem,
    IntakeRejectRequest,
    IntakeResponse,
    IntakeSubmitRequest,
    IntakeSubmitResponse,
    ReenrichmentRequest,
)
from app.services.brief_assembler import regenerate_openscad_prompt
from app.services.brief_validator import check_gate_conditions
from app.services.intake_enricher import run_enrichment
from app.services.intake_scraper import ScraperError, download_images, scrape_etsy_listing

router = APIRouter()


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------


@router.post("/submit", response_model=IntakeSubmitResponse, status_code=201)
async def submit_intake(
    payload: IntakeSubmitRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new ProductIntake record.

    - etsy_url: scrapes the listing synchronously, downloads images, then
      kicks off Stage 2 enrichment as a BackgroundTask.
    - erank_paste / manual: stores provided fields and kicks off enrichment
      if a raw_title is present.
    """
    intake = ProductIntake(
        trigger_mode=payload.trigger_mode,
        source_url=payload.source_url,
        source_keyword=payload.source_keyword,
        raw_title=payload.raw_title,
    )

    if payload.trigger_mode.value == "etsy_url":
        if not payload.source_url:
            raise HTTPException(
                status_code=422, detail="source_url is required for etsy_url mode"
            )
        try:
            scraped = scrape_etsy_listing(payload.source_url)
        except ScraperError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        intake.raw_title = scraped.get("raw_title") or payload.raw_title
        intake.raw_description = scraped.get("raw_description")
        intake.raw_tags = scraped.get("raw_tags") or []
        intake.raw_price_usd = scraped.get("raw_price_usd")
        intake.raw_review_count = scraped.get("raw_review_count")
        intake.raw_rating = scraped.get("raw_rating")

        db.add(intake)
        await db.flush()  # obtain the intake.id before downloading images

        image_urls = scraped.get("image_urls") or []
        if image_urls:
            downloaded = download_images(image_urls, intake.id)
            for i, img_data in enumerate(downloaded):
                db.add(
                    IntakeImage(
                        intake_id=intake.id,
                        image_index=i,
                        source_url=img_data["source_url"],
                        local_path=img_data["local_path"],
                        file_size_bytes=img_data["file_size_bytes"],
                    )
                )
            intake.image_count = len(downloaded)
            await db.flush()

        background_tasks.add_task(run_enrichment, intake.id)

    else:
        # erank_paste or manual — store as-is and enrich if we have text
        db.add(intake)
        await db.flush()
        if intake.raw_title:
            background_tasks.add_task(run_enrichment, intake.id)

    await db.refresh(intake)
    return IntakeSubmitResponse(intake_id=intake.id, status=intake.status)


# ---------------------------------------------------------------------------
# List & detail
# ---------------------------------------------------------------------------


@router.get("", response_model=list[IntakeListItem])
async def list_intakes(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductIntake)
        .order_by(ProductIntake.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{intake_id}", response_model=IntakeResponse)
async def get_intake(intake_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductIntake)
        .options(selectinload(ProductIntake.images))
        .where(ProductIntake.id == intake_id)
    )
    intake = result.scalar_one_or_none()
    if intake is None:
        raise HTTPException(status_code=404, detail="Intake not found")
    return intake


# ---------------------------------------------------------------------------
# Approve
# ---------------------------------------------------------------------------


@router.post("/{intake_id}/approve", response_model=IntakeApproveResponse)
async def approve_intake(
    intake_id: str,
    payload: IntakeApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve a draft brief.

    Validates all gate conditions, then creates a Product and a placeholder
    CadModel. The CadModel holds the brief parameters ready for CAD generation
    (which is queued separately — no auto-trigger in v1).
    """
    intake = await db.get(ProductIntake, intake_id)
    if intake is None:
        raise HTTPException(status_code=404, detail="Intake not found")

    brief_dict = payload.approved_brief_json.model_dump()

    gate = check_gate_conditions(brief_dict)
    if not gate.passes:
        raise HTTPException(
            status_code=422,
            detail={"message": "Brief failed gate conditions", "failures": gate.failed_conditions},
        )

    # --- Create Product -------------------------------------------------------
    name = brief_dict.get("product_type") or intake.raw_title or "Unnamed Product"
    base_slug = slugify(name)
    slug = base_slug
    suffix = 1
    while True:
        existing = await db.execute(select(Product).where(Product.slug == slug))
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    product = Product(
        name=name,
        slug=slug,
        category="3d-printed",
        source="intake",
        source_keyword=intake.source_keyword,
        status=ProductStatus.RESEARCH_ONLY,
    )
    db.add(product)
    await db.flush()

    # --- Create CadModel placeholder ------------------------------------------
    params = brief_dict.get("parametric_variables") or []
    cad_model = CadModel(
        product_id=product.id,
        version=1,
        model_type="ai_assisted",
        generation_method="ai_assisted",
        parameters_json=json.dumps(params) if params else None,
    )
    db.add(cad_model)
    await db.flush()

    # --- Update intake --------------------------------------------------------
    intake.approved_brief_json = brief_dict
    intake.status = IntakeStatus.BRIEF_APPROVED
    intake.approved_at = datetime.utcnow()
    intake.product_id = product.id
    intake.cad_model_id = cad_model.id
    if payload.reviewer_notes:
        intake.reviewer_notes = payload.reviewer_notes
    await db.flush()

    return IntakeApproveResponse(product_id=product.id, cad_model_id=cad_model.id)


# ---------------------------------------------------------------------------
# Reject
# ---------------------------------------------------------------------------


@router.post("/{intake_id}/reject")
async def reject_intake(
    intake_id: str,
    payload: IntakeRejectRequest,
    db: AsyncSession = Depends(get_db),
):
    intake = await db.get(ProductIntake, intake_id)
    if intake is None:
        raise HTTPException(status_code=404, detail="Intake not found")

    intake.status = IntakeStatus.REJECTED
    intake.rejection_reason = payload.rejection_reason
    await db.flush()

    return {"intake_id": intake_id, "status": intake.status}


# ---------------------------------------------------------------------------
# Re-enrichment
# ---------------------------------------------------------------------------


@router.post("/{intake_id}/re-enrich", status_code=202)
async def re_enrich_intake(
    intake_id: str,
    background_tasks: BackgroundTasks,
    payload: ReenrichmentRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Re-run Stage 2 enrichment for an intake.

    Allowed from any status except enriching (already running).
    Resets status to raw_collected so the enricher can proceed.
    """
    intake = await db.get(ProductIntake, intake_id)
    if intake is None:
        raise HTTPException(status_code=404, detail="Intake not found")
    if intake.status == IntakeStatus.ENRICHING:
        raise HTTPException(status_code=409, detail="Enrichment already in progress")

    intake.status = IntakeStatus.RAW_COLLECTED
    await db.flush()

    reviewer_notes = payload.reviewer_notes if payload else None
    background_tasks.add_task(run_enrichment, intake_id, reviewer_notes)

    return {"intake_id": intake_id, "status": "re_enrichment_queued"}


# ---------------------------------------------------------------------------
# Draft brief editing
# ---------------------------------------------------------------------------


@router.patch("/{intake_id}/brief", response_model=IntakeResponse)
async def update_brief_field(
    intake_id: str,
    payload: BriefFieldUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Patch a single field in draft_brief_json."""
    result = await db.execute(
        select(ProductIntake)
        .options(selectinload(ProductIntake.images))
        .where(ProductIntake.id == intake_id)
    )
    intake = result.scalar_one_or_none()
    if intake is None:
        raise HTTPException(status_code=404, detail="Intake not found")
    if intake.draft_brief_json is None:
        raise HTTPException(status_code=422, detail="No draft brief exists for this intake")

    # Reassign (not mutate in-place) so SQLAlchemy detects the change
    updated = dict(intake.draft_brief_json)
    updated[payload.field_name] = payload.field_value
    intake.draft_brief_json = updated
    await db.flush()
    await db.refresh(intake)

    return intake


# ---------------------------------------------------------------------------
# Regenerate openscad_prompt
# ---------------------------------------------------------------------------


@router.post("/{intake_id}/regenerate-prompt", response_model=IntakeResponse)
async def regenerate_prompt(
    intake_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate just the openscad_prompt field from the current brief state."""
    result = await db.execute(
        select(ProductIntake)
        .options(selectinload(ProductIntake.images))
        .where(ProductIntake.id == intake_id)
    )
    intake = result.scalar_one_or_none()
    if intake is None:
        raise HTTPException(status_code=404, detail="Intake not found")
    if not intake.draft_brief_json:
        raise HTTPException(status_code=422, detail="No draft brief available")

    new_prompt = regenerate_openscad_prompt(intake.draft_brief_json)
    if new_prompt is None:
        raise HTTPException(
            status_code=502,
            detail="Failed to regenerate prompt — check API key and logs",
        )

    updated = dict(intake.draft_brief_json)
    updated["openscad_prompt"] = new_prompt
    intake.draft_brief_json = updated
    await db.flush()
    await db.refresh(intake)

    return intake
