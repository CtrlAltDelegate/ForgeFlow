"""Opportunity score for a product."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    demand_score: Mapped[float] = mapped_column(Float, default=0.0)
    competition_score: Mapped[float] = mapped_column(Float, default=0.0)
    manufacturing_score: Mapped[float] = mapped_column(Float, default=0.0)
    margin_score: Mapped[float] = mapped_column(Float, default=0.0)
    differentiation_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    scoring_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="opportunity_scores")
