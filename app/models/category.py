from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Category(Base):
    """Catálogo de categorías de gasto. Editable por BD sin tocar código:
    agregar una fila aquí la hace aparecer en la app, el categorizador IA
    y los presupuestos por defecto."""

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # slug: "despensa"
    label: Mapped[str] = mapped_column(String, nullable=False)
    emoji: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(String, nullable=False)  # hex: "#3ECF8E"
    # Descripción con ejemplos, usada en el prompt del categorizador IA
    description: Mapped[str] = mapped_column(String, nullable=False)
    # Palabras clave separadas por coma para el fallback sin IA (mayúsculas)
    keywords: Mapped[str] = mapped_column(String, nullable=False, default="")
    default_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def keyword_list(self) -> list[str]:
        return [k.strip().upper() for k in self.keywords.split(",") if k.strip()]
