import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models import AddMemberRequest, GroupCreate, GroupRead, TransactionRead, UserRead
from app.services.expense_service import calculate_group_balances, compute_settlements
from app.store import (
    create_group,
    get_group,
    get_user,
    get_user_by_email,
    list_transactions,
    update_group_members,
)

router = APIRouter()


async def require_group_member(group_id: str, user: UserRead) -> GroupRead:
    group = await get_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    if user.id not in group.member_ids:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    return group


@router.post("/groups", status_code=201)
async def create_new_group(payload: GroupCreate, current_user: UserRead = Depends(get_current_user)) -> GroupRead:
    group = GroupRead(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        currency=payload.currency,
        member_ids=[current_user.id],
    )
    return await create_group(group)


@router.get("/groups")
async def list_my_groups(current_user: UserRead = Depends(get_current_user)) -> List[GroupRead]:
    from app.store import list_groups_for_user

    return await list_groups_for_user(current_user.id)


@router.get("/groups/{group_id}")
async def get_group_details(group_id: str, current_user: UserRead = Depends(get_current_user)) -> dict:
    group = await require_group_member(group_id, current_user)
    members = []
    for member_id in group.member_ids:
        member = await get_user(member_id)
        if member:
            members.append(UserRead(**member.model_dump(exclude={"password_hash"})))
    return {
        "group": group,
        "members": members,
        "transactions": await list_transactions(group_id),
    }


@router.post("/groups/{group_id}/members", status_code=201)
async def add_group_member(
    group_id: str,
    payload: AddMemberRequest,
    current_user: UserRead = Depends(get_current_user),
) -> GroupRead:
    group = await require_group_member(group_id, current_user)
    user = await get_user_by_email(payload.email)
    if user is None:
        raise HTTPException(status_code=404, detail="User with this email not found")
    if user.id not in group.member_ids:
        group.member_ids.append(user.id)
    updated = await update_group_members(group_id, group.member_ids)
    return updated


@router.delete("/groups/{group_id}/members/me", status_code=204)
async def leave_group(group_id: str, current_user: UserRead = Depends(get_current_user)) -> None:
    group = await require_group_member(group_id, current_user)
    if len(group.member_ids) == 1:
        raise HTTPException(status_code=400, detail="The last member cannot leave the group")
    await update_group_members(group_id, [member_id for member_id in group.member_ids if member_id != current_user.id])


@router.get("/groups/{group_id}/balances")
async def get_group_balances(group_id: str, current_user: UserRead = Depends(get_current_user)) -> dict:
    group = await require_group_member(group_id, current_user)
    balances = await calculate_group_balances(group_id)
    return {"group_id": group.id, "group_name": group.name, "members": balances}


@router.get("/groups/{group_id}/settlements")
async def get_group_settlements(group_id: str, current_user: UserRead = Depends(get_current_user)) -> dict:
    await require_group_member(group_id, current_user)
    return {"group_id": group_id, "settlements": await compute_settlements(group_id)}


@router.get("/groups/{group_id}/transactions")
async def get_group_transactions(group_id: str, current_user: UserRead = Depends(get_current_user)) -> List[TransactionRead]:
    await require_group_member(group_id, current_user)
    return await list_transactions(group_id)
