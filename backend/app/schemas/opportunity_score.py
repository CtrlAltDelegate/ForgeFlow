"""Opportunity score schemas."""
from datetime import datetime
from pydantic import BaseModel


class OpportunityScoreResponse(BaseModel):
    id: int
    product_id: int
    demand_score: float
    competition_score: float
    manufacturing_score: float
    margin_score: float
    differentiation_score: float
    total_score: float
    scoring_notes: str | None
    scored_at: datetime

    class Config:
        from_attributes = True
