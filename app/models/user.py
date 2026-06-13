import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.crypto import EncryptedString
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    picture: Mapped[str | None] = mapped_column(String, nullable=True)
    google_access_token: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    google_refresh_token: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    # % del ingreso que quiere ahorrar (0-100); ingreso × (1 - pct/100) = disponible real
    savings_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goal: Mapped["Goal | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
