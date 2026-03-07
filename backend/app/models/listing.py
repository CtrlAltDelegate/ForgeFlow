"""Marketplace listing draft for a product."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    short_pitch: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bullet_points_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    photo_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_it_could_sell: Mapped[str | None] = mapped_column(Text, nullable=True)
    differentiation_angle: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="listings")
