"""Products API routes."""
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_db
from app.models import Product, OpportunityScore, ResearchData
from app.models.product import ProductStatus, slugify
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ResearchDataSummary,
    OpportunityScoreSummary,
)

router = APIRouter()


def _research_to_summary(r: ResearchData) -> ResearchDataSummary:
    return ResearchDataSummary(
        id=r.id,
        listed_price=r.listed_price,
        review_count=r.review_count,
        rating=r.rating,
        estimated_sales=r.estimated_sales,
        competitor_count=r.competitor_count,
    )


@router.get("", response_model=list[ProductListResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = None,
    category: str | None = None,
    status: ProductStatus | None = None,
    sort: str = Query("updated_at", description="updated_at | name | opportunity_score"),
    order: str = Query("desc", description="asc | desc"),
) -> list[ProductListResponse]:
    """List products with optional filters and sorting."""
    q = select(Product)
    if search:
        q = q.where(
            Product.name.ilike(f"%{search}%") | Product.category.ilike(f"%{search}%")
        )
    if category:
        q = q.where(Product.category == category)
    if status:
        q = q.where(Product.status == status)

    if sort == "opportunity_score":
        # Subquery for latest score per product
        subq = (
            select(
                OpportunityScore.product_id,
                OpportunityScore.total_score,
                func.row_number()
                .over(
                    partition_by=OpportunityScore.product_id,
                    order_by=OpportunityScore.scored_at.desc(),
                )
                .label("rn"),
            )
            .select_from(OpportunityScore)
        ).subquery()
        q = q.outerjoin(subq, (Product.id == subq.c.product_id) & (subq.c.rn == 1))
        order_col = subq.c.total_score.desc() if order == "desc" else subq.c.total_score.asc()
        q = q.order_by(order_col.nulls_last())
    elif sort == "name":
        order_col = Product.name.desc() if order == "desc" else Product.name.asc()
        q = q.order_by(order_col)
    else:
        order_col = Product.updated_at.desc() if order == "desc" else Product.updated_at.asc()
        q = q.order_by(order_col)

    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    products = result.scalars().all()

    # Load latest opportunity score and first research row for each product
    out = []
    for p in products:
        score_result = await db.execute(
            select(OpportunityScore)
            .where(OpportunityScore.product_id == p.id)
            .order_by(OpportunityScore.scored_at.desc())
            .limit(1)
        )
        latest_score = score_result.scalar_one_or_none()
        research_result = await db.execute(
            select(ResearchData).where(ResearchData.product_id == p.id).limit(1)
        )
        first_research = research_result.scalar_one_or_none()

        estimated_price = first_research.listed_price if first_research else None
        cnt = (first_research.competitor_count or 0) if first_research else 0
        if cnt > 20:
            competition_level = "high"
        elif cnt > 5:
            competition_level = "medium"
        else:
            competition_level = "low" if first_research else None

        out.append(
            ProductListResponse(
                id=p.id,
                name=p.name,
                slug=p.slug,
                category=p.category,
                source=p.source,
                status=p.status,
                created_at=p.created_at,
                updated_at=p.updated_at,
                opportunity_score=float(latest_score.total_score) if latest_score else None,
                estimated_price=estimated_price,
                competition_level=competition_level,
                manufacturing_difficulty=None,
                profit_margin_estimate=None,
            )
        )
    return out


@router.get("/categories", response_model=list[str])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[str]:
    """List distinct product categories."""
    result = await db.execute(select(Product.category).distinct().order_by(Product.category))
    return [r[0] for r in result.all()]


@router.get("/{product_id_or_slug}", response_model=ProductResponse)
async def get_product(
    product_id_or_slug: str,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """Get a single product by ID or slug."""
    try:
        product_id = int(product_id_or_slug)
        q = select(Product).where(Product.id == product_id)
    except ValueError:
        q = select(Product).where(Product.slug == product_id_or_slug)

    result = await db.execute(
        q.options(
            selectinload(Product.research_data),
            selectinload(Product.opportunity_scores),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    latest_score = None
    if product.opportunity_scores:
        latest_score = max(product.opportunity_scores, key=lambda s: s.scored_at)

    return ProductResponse(
        id=product.id,
        name=product.name,
        slug=product.slug,
        category=product.category,
        source=product.source,
        source_keyword=product.source_keyword,
        source_notes=product.source_notes,
        status=product.status,
        created_at=product.created_at,
        updated_at=product.updated_at,
        research_data=[_research_to_summary(r) for r in product.research_data],
        latest_opportunity_score=OpportunityScoreSummary(
            id=latest_score.id,
            total_score=latest_score.total_score,
            demand_score=latest_score.demand_score,
            competition_score=latest_score.competition_score,
            manufacturing_score=latest_score.manufacturing_score,
            margin_score=latest_score.margin_score,
            differentiation_score=latest_score.differentiation_score,
            scored_at=latest_score.scored_at,
        )
        if latest_score
        else None,
    )


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """Create a new product."""
    base_slug = slugify(payload.name)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(select(Product).where(Product.slug == slug))
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    product = Product(
        name=payload.name,
        slug=slug,
        category=payload.category,
        source=payload.source,
        source_keyword=payload.source_keyword,
        source_notes=payload.source_notes,
        status=payload.status,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return ProductResponse(
        id=product.id,
        name=product.name,
        slug=product.slug,
        category=product.category,
        source=product.source,
        source_keyword=product.source_keyword,
        source_notes=product.source_notes,
        status=product.status,
        created_at=product.created_at,
        updated_at=product.updated_at,
        research_data=[],
        latest_opportunity_score=None,
    )


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """Update a product."""
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.research_data),
            selectinload(Product.opportunity_scores),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.name is not None:
        product.name = payload.name
        product.slug = slugify(payload.name)
    if payload.category is not None:
        product.category = payload.category
    if payload.source is not None:
        product.source = payload.source
    if payload.source_keyword is not None:
        product.source_keyword = payload.source_keyword
    if payload.source_notes is not None:
        product.source_notes = payload.source_notes
    if payload.status is not None:
        product.status = payload.status

    await db.flush()
    await db.refresh(product)

    latest_score = None
    if product.opportunity_scores:
        latest_score = max(product.opportunity_scores, key=lambda s: s.scored_at)

    return ProductResponse(
        id=product.id,
        name=product.name,
        slug=product.slug,
        category=product.category,
        source=product.source,
        source_keyword=product.source_keyword,
        source_notes=product.source_notes,
        status=product.status,
        created_at=product.created_at,
        updated_at=product.updated_at,
        research_data=[_research_to_summary(r) for r in product.research_data],
        latest_opportunity_score=OpportunityScoreSummary(
            id=latest_score.id,
            total_score=latest_score.total_score,
            demand_score=latest_score.demand_score,
            competition_score=latest_score.competition_score,
            manufacturing_score=latest_score.manufacturing_score,
            margin_score=latest_score.margin_score,
            differentiation_score=latest_score.differentiation_score,
            scored_at=latest_score.scored_at,
        )
        if latest_score
        else None,
    )


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(product)
    await db.flush()
