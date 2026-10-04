import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models import TransactionCreate, TransactionRead, TransactionUpdate, UserRead
from app.routes.groups import require_group_member
from app.store import (
    create_transaction,
    delete_transaction,
    get_transaction,
    get_user,
    update_transaction,
)

router = APIRouter()


@router.post("/groups/{group_id}/transactions", status_code=201)
async def create_group_transaction(
    group_id: str,
    payload: TransactionCreate,
    current_user: UserRead = Depends(get_current_user),
) -> TransactionRead:
    group = await require_group_member(group_id, current_user)
    split_members = list(dict.fromkeys(payload.split_between or group.member_ids))
    if any(member_id not in group.member_ids for member_id in split_members):
        raise HTTPException(status_code=400, detail="Every split member must belong to the group")

    if payload.transaction_type == "reimbursement":
        if payload.to_user_id is None or payload.to_user_id not in group.member_ids:
            raise HTTPException(status_code=400, detail="A reimbursement recipient must be a group member")
        if payload.to_user_id == current_user.id:
            raise HTTPException(status_code=400, detail="You cannot reimburse yourself")
        split_members = [current_user.id, payload.to_user_id]
    elif payload.to_user_id is not None:
        raise HTTPException(status_code=400, detail="Only reimbursements can specify a recipient")

    transaction = TransactionRead(
        id=str(uuid.uuid4()),
        group_id=group_id,
        title=payload.title.strip(),
        amount=payload.amount,
        transaction_type=payload.transaction_type,
        paid_by=current_user.id,
        split_between=split_members,
        to_user_id=payload.to_user_id,
        category=payload.category.strip() if payload.category else None,
        notes=payload.notes.strip() if payload.notes else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return await create_transaction(transaction)


@router.patch("/transactions/{transaction_id}")
async def edit_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    current_user: UserRead = Depends(get_current_user),
) -> TransactionRead:
    transaction = await get_transaction(transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.paid_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the transaction owner can edit it")

    group = await require_group_member(transaction.group_id, current_user)

    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "amount" in updates and updates["amount"] <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")
    if "split_between" in updates:
        split_members = list(dict.fromkeys(updates["split_between"] or group.member_ids))
        if any(member_id not in group.member_ids for member_id in split_members):
            raise HTTPException(status_code=400, detail="Every split member must belong to the group")
        updates["split_between"] = split_members
    if "to_user_id" in updates and updates["to_user_id"] not in group.member_ids:
        raise HTTPException(status_code=400, detail="Reimbursement recipient must belong to the group")
    if transaction.transaction_type == "expense" and "to_user_id" in updates:
        raise HTTPException(status_code=400, detail="Only reimbursements can specify a recipient")
    updated = await update_transaction(transaction_id, updates)
    return updated


@router.delete("/transactions/{transaction_id}", status_code=204)
async def remove_transaction(transaction_id: str, current_user: UserRead = Depends(get_current_user)) -> None:
    transaction = await get_transaction(transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.paid_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the transaction owner can delete it")
    await delete_transaction(transaction_id)
