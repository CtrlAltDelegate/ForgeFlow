"""Pydantic schemas for the product intake pipeline (Section 6 of spec)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.intake import IntakeStatus, TriggerMode
from app.schemas.brief import ProductBrief


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------


class IntakeSubmitRequest(BaseModel):
    trigger_mode: TriggerMode
    source_url: str | None = None       # Etsy listing URL (etsy_url mode)
    source_keyword: str | None = None   # eRank keyword (erank_paste mode)
    raw_title: str | None = None        # Optional pre-filled title


class IntakeSubmitResponse(BaseModel):
    intake_id: str
    status: IntakeStatus


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------


class IntakeImageResponse(BaseModel):
    id: str
    intake_id: str
    image_index: int | None
    source_url: str | None
    local_path: str
    file_size_bytes: int | None
    vision_analysis_json: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Intake record — list + detail
# ---------------------------------------------------------------------------


class IntakeListItem(BaseModel):
    """Lightweight representation for the queue view."""

    id: str
    status: IntakeStatus
    trigger_mode: TriggerMode
    raw_title: str | None
    source_url: str | None
    source_keyword: str | None
    confidence_score: float | None
    image_count: int
    enrichment_attempt_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntakeResponse(BaseModel):
    """Full intake record returned by GET /api/intake/{id}."""

    id: str
    status: IntakeStatus
    trigger_mode: TriggerMode
    source_url: str | None
    source_keyword: str | None
    raw_title: str | None
    raw_description: str | None
    raw_tags: Any | None
    raw_price_usd: float | None
    raw_review_count: int | None
    raw_rating: float | None
    image_count: int
    visual_summary_json: Any | None
    text_extraction_json: Any | None
    draft_brief_json: Any | None
    approved_brief_json: Any | None
    confidence_score: float | None
    confidence_detail_json: Any | None
    enrichment_attempt_count: int
    reviewer_notes: str | None
    approved_by: str | None
    approved_at: datetime | None
    rejection_reason: str | None
    product_id: int | None
    cad_model_id: int | None
    created_at: datetime
    updated_at: datetime
    images: list[IntakeImageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------


class IntakeApproveRequest(BaseModel):
    approved_brief_json: ProductBrief
    reviewer_notes: str | None = None


class IntakeApproveResponse(BaseModel):
    product_id: int
    cad_model_id: int


# ---------------------------------------------------------------------------
# Rejection & re-enrichment
# ---------------------------------------------------------------------------


class IntakeRejectRequest(BaseModel):
    rejection_reason: str = Field(min_length=1)


class ReenrichmentRequest(BaseModel):
    reviewer_notes: str | None = None


# ---------------------------------------------------------------------------
# Draft brief editing
# ---------------------------------------------------------------------------


class BriefFieldUpdate(BaseModel):
    """PATCH /api/intake/{id}/draft-brief — update a single field."""

    field_name: str
    field_value: Any
