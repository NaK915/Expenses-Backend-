from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserInDB(UserRead):
    password_hash: str
