"""Product model."""
import re
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Index
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ProductStatus(str, enum.Enum):
    RESEARCH_ONLY = "research_only"
    SCORED = "scored"
    CAD_GENERATED = "cad_generated"
    MANUFACTURING_SIMULATED = "manufacturing_simulated"
    LISTING_GENERATED = "listing_generated"
    PROTOTYPE_CANDIDATE = "prototype_candidate"
    ARCHIVED = "archived"


def slugify(text: str) -> str:
    """Generate URL-safe slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:80].strip("-")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), default="manual")
    source_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProductStatus.RESEARCH_ONLY,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    research_data: Mapped[list["ResearchData"]] = relationship(
        "ResearchData", back_populates="product", cascade="all, delete-orphan"
    )
    opportunity_scores: Mapped[list["OpportunityScore"]] = relationship(
        "OpportunityScore", back_populates="product", cascade="all, delete-orphan"
    )
    cad_models: Mapped[list["CadModel"]] = relationship(
        "CadModel", back_populates="product", cascade="all, delete-orphan"
    )
    manufacturing_simulations: Mapped[list["ManufacturingSimulation"]] = relationship(
        "ManufacturingSimulation", back_populates="product", cascade="all, delete-orphan"
    )
    listings: Mapped[list["Listing"]] = relationship(
        "Listing", back_populates="product", cascade="all, delete-orphan"
    )
    notes: Mapped[list["ProductNote"]] = relationship(
        "ProductNote", back_populates="product", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_products_status_updated", "status", "updated_at"),)
