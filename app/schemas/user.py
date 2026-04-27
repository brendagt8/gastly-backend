from pydantic import BaseModel
from datetime import datetime


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    picture: str | None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
