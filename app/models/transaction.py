import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    # Los message IDs de Gmail son por buzón, así que la unicidad es por usuario
    __table_args__ = (UniqueConstraint("user_id", "email_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    merchant: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False, default="otros")
    bank: Mapped[str] = mapped_column(String, nullable=False, default="Desconocido")
    card_last4: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    email_id: Mapped[str | None] = mapped_column(String, nullable=True)  # Gmail message ID
    recategorized: Mapped[bool] = mapped_column(Boolean, default=False)
    manual: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="transactions")
