from pydantic import BaseModel, Field
from datetime import datetime


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    picture: str | None
    monthly_income: float | None
    savings_percent: float | None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    monthly_income: float | None = Field(default=None, gt=0)
    savings_percent: float | None = Field(default=None, ge=0, lt=100)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
