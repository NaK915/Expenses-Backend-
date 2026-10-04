import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.models import UserInDB, UserRead
from app.models.auth import AuthTokenResponse, LoginRequest, RegisterRequest
from app.store import create_user, get_user_by_email

router = APIRouter(prefix="/auth")


@router.post("/register", status_code=201, response_model=AuthTokenResponse)
async def register_user(payload: RegisterRequest):
    if await get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user = UserInDB(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
    )
    public_user = await create_user(user)

    token = create_access_token(user.id)
    return {"user": public_user, "access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=AuthTokenResponse)
async def login_user(payload: LoginRequest):
    user = await get_user_by_email(payload.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return {
        "user": UserRead(**user.model_dump(exclude={"password_hash"})),
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(current_user: UserRead = Depends(get_current_user)):
    return UserRead(**current_user.model_dump(exclude={"password_hash"}))
