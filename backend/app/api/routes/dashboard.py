"""Dashboard API routes."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models import Product, OpportunityScore, ResearchData, CadModel, Listing, ManufacturingSimulation
from app.models.product import ProductStatus
from app.schemas.dashboard import (
    DashboardSummary,
    PipelineStageCounts,
    TopOpportunitySummary,
    RecentActivityItem,
)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    """Get dashboard summary: counts, top opportunities, recent activity."""
    # Total products
    total_result = await db.execute(select(func.count(Product.id)))
    total_products = total_result.scalar_one() or 0

    # Pipeline stage counts
    status_counts = await db.execute(
        select(Product.status, func.count(Product.id)).group_by(Product.status)
    )
    rows = status_counts.all()
    stage_counts = PipelineStageCounts(
        research_only=next((r[1] for r in rows if r[0] == ProductStatus.RESEARCH_ONLY), 0),
        scored=next((r[1] for r in rows if r[0] == ProductStatus.SCORED), 0),
        cad_generated=next((r[1] for r in rows if r[0] == ProductStatus.CAD_GENERATED), 0),
        manufacturing_simulated=next(
            (r[1] for r in rows if r[0] == ProductStatus.MANUFACTURING_SIMULATED), 0
        ),
        listing_generated=next((r[1] for r in rows if r[0] == ProductStatus.LISTING_GENERATED), 0),
        prototype_candidate=next(
            (r[1] for r in rows if r[0] == ProductStatus.PROTOTYPE_CANDIDATE), 0
        ),
        archived=next((r[1] for r in rows if r[0] == ProductStatus.ARCHIVED), 0),
    )

    # Average opportunity score (from latest score per product)
    subq = (
        select(
            OpportunityScore.product_id,
            OpportunityScore.total_score,
            func.row_number()
            .over(partition_by=OpportunityScore.product_id, order_by=OpportunityScore.scored_at.desc())
            .label("rn"),
        )
        .select_from(OpportunityScore)
    ).subquery()
    avg_score_result = await db.execute(
        select(func.avg(subq.c.total_score)).select_from(subq).where(subq.c.rn == 1)
    )
    average_opportunity_score = avg_score_result.scalar_one()

    # Average margin and print time (placeholder - from manufacturing_simulations when we have data)
    avg_margin_result = await db.execute(
        select(func.avg(ManufacturingSimulation.estimated_filament_cost)).select_from(
            ManufacturingSimulation
        )
    )
    average_estimated_margin = avg_margin_result.scalar_one()
    avg_time_result = await db.execute(
        select(func.avg(ManufacturingSimulation.estimated_print_time_minutes)).select_from(
            ManufacturingSimulation
        )
    )
    average_estimated_print_time_minutes = avg_time_result.scalar_one()

    # Top 10 opportunities (by latest total_score)
    top_scores_subq = (
        select(
            OpportunityScore.product_id,
            OpportunityScore.total_score,
            func.row_number()
            .over(partition_by=OpportunityScore.product_id, order_by=OpportunityScore.scored_at.desc())
            .label("rn"),
        )
        .select_from(OpportunityScore)
    ).subquery()
    top_scores = (
        select(Product.id, Product.name, Product.slug, Product.category, top_scores_subq.c.total_score)
        .join(top_scores_subq, Product.id == top_scores_subq.c.product_id)
        .where(top_scores_subq.c.rn == 1)
        .order_by(top_scores_subq.c.total_score.desc())
        .limit(10)
    )
    top_result = await db.execute(top_scores)
    top_rows = top_result.all()
    top_opportunities = [
        TopOpportunitySummary(
            id=r.id, name=r.name, slug=r.slug, total_score=float(r.total_score), category=r.category
        )
        for r in top_rows
    ]

    top_opportunity = top_opportunities[0] if top_opportunities else None
    fastest_to_manufacture = None  # Phase 4
    highest_margin = None  # Phase 4
    most_differentiable = None  # Phase 4

    # Recent activity: last 5 products updated (as proxy for "recent imports/cad/listings")
    recent_products = (
        select(Product.id, Product.name, Product.slug, Product.updated_at)
        .order_by(Product.updated_at.desc())
        .limit(15)
    )
    recent_result = await db.execute(recent_products)
    recent_rows = recent_result.all()
    recent_imports = [
        RecentActivityItem(id=r.id, name=r.name, slug=r.slug, type="import", at=r.updated_at)
        for r in recent_rows[:5]
    ]
    recent_cad_generations = [
        RecentActivityItem(id=r.id, name=r.name, slug=r.slug, type="cad", at=r.updated_at)
        for r in recent_rows[5:10]
    ]
    recent_listing_generations = [
        RecentActivityItem(id=r.id, name=r.name, slug=r.slug, type="listing", at=r.updated_at)
        for r in recent_rows[10:15]
    ]

    return DashboardSummary(
        total_products=total_products,
        average_opportunity_score=float(average_opportunity_score) if average_opportunity_score is not None else None,
        average_estimated_margin=float(average_estimated_margin) if average_estimated_margin is not None else None,
        average_estimated_print_time_minutes=float(average_estimated_print_time_minutes)
        if average_estimated_print_time_minutes is not None
        else None,
        pipeline_stage_counts=stage_counts,
        top_opportunities=top_opportunities,
        top_opportunity=top_opportunity,
        fastest_to_manufacture=fastest_to_manufacture,
        highest_margin=highest_margin,
        most_differentiable=most_differentiable,
        recent_imports=recent_imports,
        recent_cad_generations=recent_cad_generations,
        recent_listing_generations=recent_listing_generations,
    )
