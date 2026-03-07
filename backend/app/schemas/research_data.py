"""Research data schemas."""
from datetime import datetime
from pydantic import BaseModel


class ResearchDataBase(BaseModel):
    source_type: str = "manual"
    keyword: str | None = None
    listed_price: float | None = None
    review_count: int | None = None
    rating: float | None = None
    estimated_sales: int | None = None
    competitor_count: int | None = None
    listing_count: int | None = None
    listing_age_days: int | None = None
    notes: str | None = None


class ResearchDataCreate(ResearchDataBase):
    product_id: int


class ResearchDataResponse(ResearchDataBase):
    id: int
    product_id: int
    imported_at: datetime

    class Config:
        from_attributes = True
