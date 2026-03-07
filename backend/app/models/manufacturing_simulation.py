"""Manufacturing simulation result for a product."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ManufacturingSimulation(Base):
    __tablename__ = "manufacturing_simulations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    cad_model_id: Mapped[int | None] = mapped_column(ForeignKey("cad_models.id", ondelete="SET NULL"), nullable=True)
    material_type: Mapped[str] = mapped_column(String(50), default="PLA")
    layer_height: Mapped[float] = mapped_column(Float, default=0.2)
    infill: Mapped[float] = mapped_column(Float, default=20.0)
    nozzle_size: Mapped[float] = mapped_column(Float, default=0.4)
    estimated_print_time_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_material_grams: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_filament_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    supports_required: Mapped[bool] = mapped_column(default=False)
    recommended_orientation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    simulated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="manufacturing_simulations")
