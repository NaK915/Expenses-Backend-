from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    preferred_currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserInDB(UserRead):
    password_hash: str


class UserPreferencesUpdate(BaseModel):
    preferred_currency: str = Field(pattern=r"^[A-Z]{3}$")
