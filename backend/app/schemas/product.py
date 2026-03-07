"""Product Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.product import ProductStatus


class ProductBase(BaseModel):
    name: str
    category: str
    source: str = "manual"
    source_keyword: str | None = None
    source_notes: str | None = None
    status: ProductStatus = ProductStatus.RESEARCH_ONLY


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    source: str | None = None
    source_keyword: str | None = None
    source_notes: str | None = None
    status: ProductStatus | None = None


class ResearchDataSummary(BaseModel):
    id: int
    listed_price: float | None
    review_count: int | None
    rating: float | None
    estimated_sales: int | None
    competitor_count: int | None

    class Config:
        from_attributes = True


class OpportunityScoreSummary(BaseModel):
    id: int
    total_score: float
    demand_score: float
    competition_score: float
    manufacturing_score: float
    margin_score: float
    differentiation_score: float
    scored_at: datetime

    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
    research_data: list[ResearchDataSummary] = Field(default_factory=list)
    latest_opportunity_score: OpportunityScoreSummary | None = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    id: int
    name: str
    slug: str
    category: str
    source: str
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    opportunity_score: float | None = None
    estimated_price: float | None = None
    competition_level: str | None = None
    manufacturing_difficulty: str | None = None
    profit_margin_estimate: float | None = None

    class Config:
        from_attributes = True
