from pydantic import BaseModel
from datetime import datetime


class BudgetSet(BaseModel):
    amount: float


class BudgetOut(BaseModel):
    id: str
    category: str
    amount: float
    month: str
    updated_at: datetime

    model_config = {"from_attributes": True}
