"""ProductIntake and IntakeImage models for the intake pipeline."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.core.database import Base


class IntakeStatus(str, enum.Enum):
    RAW_COLLECTED = "raw_collected"
    ENRICHING = "enriching"
    BRIEF_DRAFTED = "brief_drafted"
    BRIEF_APPROVED = "brief_approved"
    REJECTED = "rejected"
    CAD_QUEUED = "cad_queued"


class TriggerMode(str, enum.Enum):
    ETSY_URL = "etsy_url"
    ERANK_PASTE = "erank_paste"
    MANUAL = "manual"


class ProductIntake(Base):
    """Tracks a product from raw discovery through brief approval."""

    __tablename__ = "product_intakes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Pipeline state
    status: Mapped[IntakeStatus] = mapped_column(
        SQLEnum(IntakeStatus, values_callable=lambda x: [e.value for e in x]),
        default=IntakeStatus.RAW_COLLECTED,
        nullable=False,
        index=True,
    )
    trigger_mode: Mapped[TriggerMode] = mapped_column(
        SQLEnum(TriggerMode, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    # Stage 1 — raw discovery fields
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_keyword: Mapped[str | None] = mapped_column(String(256), nullable=True)
    raw_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_count: Mapped[int] = mapped_column(Integer, default=0)

    # Stage 2 — enrichment outputs
    visual_summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    text_extraction_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    draft_brief_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_detail_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    enrichment_attempt_count: Mapped[int] = mapped_column(Integer, default=0)

    # Stage 3 — human review
    approved_brief_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Links to downstream records (set after approval)
    product_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    cad_model_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("cad_models.id", ondelete="SET NULL"),
        nullable=True,
    )

    images: Mapped[list["IntakeImage"]] = relationship(
        "IntakeImage", back_populates="intake", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_product_intakes_status_created", "status", "created_at"),
    )


class IntakeImage(Base):
    """Stores metadata and local path for each image collected during Stage 1."""

    __tablename__ = "intake_images"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    intake_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("product_intakes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    local_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vision_analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    intake: Mapped["ProductIntake"] = relationship(
        "ProductIntake", back_populates="images"
    )
