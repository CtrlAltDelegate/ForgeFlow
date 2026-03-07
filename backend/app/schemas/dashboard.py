"""Dashboard summary schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineStageCounts(BaseModel):
    research_only: int = 0
    scored: int = 0
    cad_generated: int = 0
    manufacturing_simulated: int = 0
    listing_generated: int = 0
    prototype_candidate: int = 0
    archived: int = 0


class TopOpportunitySummary(BaseModel):
    id: int
    name: str
    slug: str
    total_score: float
    category: str


class RecentActivityItem(BaseModel):
    id: int
    name: str
    slug: str
    type: str  # "import" | "cad" | "listing" | "simulation"
    at: datetime


class DashboardSummary(BaseModel):
    total_products: int = 0
    average_opportunity_score: float | None = None
    average_estimated_margin: float | None = None
    average_estimated_print_time_minutes: float | None = None
    pipeline_stage_counts: PipelineStageCounts = PipelineStageCounts()
    top_opportunities: list[TopOpportunitySummary] = Field(default_factory=list)
    top_opportunity: TopOpportunitySummary | None = None
    fastest_to_manufacture: TopOpportunitySummary | None = None
    highest_margin: TopOpportunitySummary | None = None
    most_differentiable: TopOpportunitySummary | None = None
    recent_imports: list[RecentActivityItem] = Field(default_factory=list)
    recent_cad_generations: list[RecentActivityItem] = Field(default_factory=list)
    recent_listing_generations: list[RecentActivityItem] = Field(default_factory=list)


