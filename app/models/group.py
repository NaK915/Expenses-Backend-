from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")


class AddMemberRequest(BaseModel):
    email: str


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    member_ids: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
