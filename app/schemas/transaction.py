from datetime import date as DateType, datetime
from pydantic import BaseModel
from typing import Literal, Optional

Category = Literal["despensa", "salidas", "gasolina", "salud", "suscripciones", "ropa", "otros"]


class TransactionCreate(BaseModel):
    merchant: str
    amount: float
    category: Category
    tx_date: Optional[DateType] = None  # defaults to today if not provided


class TransactionCategoryUpdate(BaseModel):
    category: Category


class TransactionOut(BaseModel):
    id: str
    merchant: str
    amount: float
    category: str
    bank: str
    card_last4: Optional[str]
    date: DateType
    recategorized: bool
    manual: bool
    created_at: datetime

    model_config = {"from_attributes": True}
