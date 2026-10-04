from pydantic import BaseModel, Field

from app.models.user import UserRead


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthTokenResponse(BaseModel):
    user: UserRead
    access_token: str
    token_type: str = "bearer"
