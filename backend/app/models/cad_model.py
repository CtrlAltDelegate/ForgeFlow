"""CAD model (OpenSCAD) linked to a product."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CadModel(Base):
    __tablename__ = "cad_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    scad_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    scad_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    stl_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    generation_method: Mapped[str] = mapped_column(String(50), default="template")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="cad_models")
