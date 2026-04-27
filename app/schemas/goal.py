from pydantic import BaseModel
from datetime import datetime


class GoalSet(BaseModel):
    description: str


class GoalOut(BaseModel):
    id: str
    description: str
    updated_at: datetime

    model_config = {"from_attributes": True}
