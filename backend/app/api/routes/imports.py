"""Imports and CSV upload API."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse

from app.core.database import get_db
from app.models import Product, ResearchData, ImportRecord
from app.models.product import ProductStatus, slugify
from app.services.import_service import (
    parse_csv,
    get_csv_template,
)
from app.schemas.import_schema import ImportRecordResponse, ImportListResponse

router = APIRouter()


@router.get("/template", response_class=PlainTextResponse)
def download_csv_template() -> str:
    """Download CSV template for product research import."""
    return get_csv_template()


@router.post("/preview")
async def preview_csv(
    file: UploadFile = File(...),
) -> dict:
    """
    Parse and validate CSV without saving. Returns parsed rows and any errors.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    content = await file.read()
    rows, errors = parse_csv(content)
    return {
        "valid": len(errors) == 0,
        "row_count": len(rows),
        "errors": [{"row": e.row, "message": e.message} for e in errors],
        "preview": [
            {
                "name": r.name,
                "category": r.category,
                "source": r.source,
                "listed_price": r.listed_price,
                "review_count": r.review_count,
                "rating": r.rating,
                "estimated_sales": r.estimated_sales,
                "competitor_count": r.competitor_count,
            }
            for r in rows[:20]
        ],
    }


async def _ensure_slug_unique(db: AsyncSession, base_slug: str) -> str:
    slug = base_slug
    n = 1
    while True:
        result = await db.execute(select(Product).where(Product.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}-{n}"
        n += 1


@router.post("/upload", response_model=ImportRecordResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ImportRecordResponse:
    """
    Upload CSV: parse, create products + research_data, log import.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    content = await file.read()
    rows, errors = parse_csv(content)
    if errors:
        raise HTTPException(
            status_code=400,
            detail={"message": "CSV validation failed", "errors": [{"row": e.row, "message": e.message} for e in errors]},
        )

    imp = ImportRecord(
        file_name=file.filename,
        source_type="csv",
        record_count=len(rows),
        status="processing",
        notes=None,
    )
    db.add(imp)
    await db.flush()

    created = 0
    for r in rows:
        base_slug = slugify(r.name)
        slug = await _ensure_slug_unique(db, base_slug)
        product = Product(
            name=r.name,
            slug=slug,
            category=r.category,
            source=r.source,
            source_keyword=r.source_keyword,
            source_notes=r.source_notes,
            status=ProductStatus.RESEARCH_ONLY,
        )
        db.add(product)
        await db.flush()

        research = ResearchData(
            product_id=product.id,
            source_type="csv",
            keyword=r.source_keyword,
            listed_price=r.listed_price,
            review_count=r.review_count,
            rating=r.rating,
            estimated_sales=r.estimated_sales,
            competitor_count=r.competitor_count,
            listing_count=r.listing_count,
            listing_age_days=r.listing_age_days,
            notes=r.notes,
        )
        db.add(research)
        created += 1

    imp.status = "completed"
    imp.notes = f"Created {created} products."
    await db.flush()
    await db.refresh(imp)

    return ImportRecordResponse(
        id=imp.id,
        file_name=imp.file_name,
        source_type=imp.source_type,
        record_count=imp.record_count,
        status=imp.status,
        notes=imp.notes,
        imported_at=imp.imported_at,
    )


@router.get("", response_model=list[ImportListResponse])
async def list_imports(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
) -> list[ImportListResponse]:
    """List recent imports."""
    from sqlalchemy import desc
    result = await db.execute(
        select(ImportRecord).order_by(desc(ImportRecord.imported_at)).limit(limit)
    )
    records = result.scalars().all()
    return [
        ImportListResponse(
            id=r.id,
            file_name=r.file_name,
            source_type=r.source_type,
            record_count=r.record_count,
            status=r.status,
            imported_at=r.imported_at,
        )
        for r in records
    ]


@router.get("/{import_id}", response_model=ImportRecordResponse)
async def get_import(
    import_id: int,
    db: AsyncSession = Depends(get_db),
) -> ImportRecordResponse:
    """Get a single import record."""
    result = await db.execute(select(ImportRecord).where(ImportRecord.id == import_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Import not found")
    return ImportRecordResponse(
        id=r.id,
        file_name=r.file_name,
        source_type=r.source_type,
        record_count=r.record_count,
        status=r.status,
        notes=r.notes,
        imported_at=r.imported_at,
    )
