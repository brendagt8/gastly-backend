from datetime import date as DateType, datetime
from pydantic import BaseModel
from typing import Optional


# La categoría se valida contra la tabla categories en cada ruta,
# no con un Literal hardcodeado
class TransactionCreate(BaseModel):
    merchant: str
    amount: float
    category: str
    tx_date: Optional[DateType] = None  # defaults to today if not provided


class TransactionCategoryUpdate(BaseModel):
    category: str


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
