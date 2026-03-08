"""Listing generation API."""
import json
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.models import Product, Listing
from app.models.product import ProductStatus
from app.schemas.listing_schema import ListingResponse, ListingUpdate
from app.services.listing_service import generate_listing, ListingInputs

router = APIRouter()


def _listing_to_response(l: Listing) -> ListingResponse:
    return ListingResponse(
        id=l.id,
        product_id=l.product_id,
        version=l.version,
        title=l.title,
        short_pitch=l.short_pitch,
        bullet_points_json=l.bullet_points_json,
        description=l.description,
        tags_json=l.tags_json,
        suggested_price=l.suggested_price,
        photo_prompt=l.photo_prompt,
        why_it_could_sell=l.why_it_could_sell,
        differentiation_angle=l.differentiation_angle,
        created_at=l.created_at,
    )


@router.get("/{product_id}/listings", response_model=list[ListingResponse])
async def list_listings(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ListingResponse]:
    """List listing drafts for a product."""
    result = await db.execute(
        select(Listing).where(Listing.product_id == product_id).order_by(Listing.version.desc())
    )
    listings = result.scalars().all()
    return [_listing_to_response(l) for l in listings]


@router.post("/{product_id}/listings", response_model=ListingResponse, status_code=201)
async def create_listing(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> ListingResponse:
    """Generate and save a new listing draft from product + research data."""
    result = await db.execute(
        select(Product).where(Product.id == product_id).options(
            selectinload(Product.research_data),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    research = product.research_data[0] if product.research_data else None
    inputs = ListingInputs(
        product_name=product.name,
        category=product.category,
        listed_price=research.listed_price if research else None,
        competitor_count=research.competitor_count if research else None,
        review_count=research.review_count if research else None,
        rating=research.rating if research else None,
        source_keyword=product.source_keyword,
        notes=research.notes if research else None,
    )
    gen = generate_listing(inputs)

    count_result = await db.execute(select(Listing).where(Listing.product_id == product_id))
    version = len(count_result.scalars().all()) + 1

    listing = Listing(
        product_id=product_id,
        version=version,
        title=gen.title,
        short_pitch=gen.short_pitch,
        bullet_points_json=json.dumps(gen.bullet_points),
        description=gen.description,
        tags_json=json.dumps(gen.tags),
        suggested_price=gen.suggested_price,
        photo_prompt=gen.photo_prompt,
        why_it_could_sell=gen.why_it_could_sell,
        differentiation_angle=gen.differentiation_angle,
    )
    db.add(listing)
    product.status = ProductStatus.LISTING_GENERATED
    await db.flush()
    await db.refresh(listing)
    return _listing_to_response(listing)


@router.get("/{product_id}/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(
    product_id: int,
    listing_id: int,
    db: AsyncSession = Depends(get_db),
) -> ListingResponse:
    """Get a single listing draft."""
    result = await db.execute(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.product_id == product_id,
        )
    )
    l = result.scalar_one_or_none()
    if not l:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _listing_to_response(l)


@router.patch("/{product_id}/listings/{listing_id}", response_model=ListingResponse)
async def update_listing(
    product_id: int,
    listing_id: int,
    payload: ListingUpdate,
    db: AsyncSession = Depends(get_db),
) -> ListingResponse:
    """Update a listing draft (manual edit)."""
    result = await db.execute(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.product_id == product_id,
        )
    )
    l = result.scalar_one_or_none()
    if not l:
        raise HTTPException(status_code=404, detail="Listing not found")
    if payload.title is not None:
        l.title = payload.title
    if payload.short_pitch is not None:
        l.short_pitch = payload.short_pitch
    if payload.bullet_points_json is not None:
        l.bullet_points_json = payload.bullet_points_json
    if payload.description is not None:
        l.description = payload.description
    if payload.tags_json is not None:
        l.tags_json = payload.tags_json
    if payload.suggested_price is not None:
        l.suggested_price = payload.suggested_price
    if payload.photo_prompt is not None:
        l.photo_prompt = payload.photo_prompt
    if payload.why_it_could_sell is not None:
        l.why_it_could_sell = payload.why_it_could_sell
    if payload.differentiation_angle is not None:
        l.differentiation_angle = payload.differentiation_angle
    await db.flush()
    await db.refresh(l)
    return _listing_to_response(l)
