"""Research data linked to a product."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResearchData(Base):
    __tablename__ = "research_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="manual")
    keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    listed_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_sales: Mapped[int | None] = mapped_column(Integer, nullable=True)
    competitor_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    listing_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    listing_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="research_data")
