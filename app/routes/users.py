from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models import UserRead
from app.store import get_user, list_users

router = APIRouter()


@router.get("/users")
async def get_users(current_user: UserRead = Depends(get_current_user)) -> List[UserRead]:
    return await list_users()


@router.get("/users/me")
async def get_profile(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    return current_user


@router.get("/users/{user_id}")
async def get_user_profile(user_id: str, current_user: UserRead = Depends(get_current_user)) -> UserRead:
    user = await get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead(**user.model_dump(exclude={"password_hash"}))
