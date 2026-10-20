import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from app.auth import get_current_user
from app.models import TransactionCreate, TransactionRead, TransactionUpdate, UserRead
from app.routes.groups import require_group_member
from app.services.expense_service import calculate_split_allocations
from app.services.llm import categorize_expense
from app.store import (
    create_transaction,
    delete_transaction,
    get_transaction,
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

    if payload.transaction_type == "expense":
        try:
            allocations = calculate_split_allocations(
                payload.amount,
                split_members,
                payload.split_type,
                payload.split_amounts,
                payload.split_parts,
            )
        except (ValueError, ArithmeticError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        allocations = {}

    category = payload.category.strip() if payload.category and payload.category.strip() else None
    if payload.transaction_type == "expense" and category is None:
        category = await run_in_threadpool(
            categorize_expense,
            payload.title,
            payload.description or "",
        )

    transaction = TransactionRead(
        id=str(uuid.uuid4()),
        group_id=group_id,
        title=payload.title.strip(),
        amount=payload.amount,
        transaction_type=payload.transaction_type,
        paid_by=current_user.id,
        split_between=split_members,
        split_type=payload.split_type if payload.transaction_type == "expense" else "equal",
        split_amounts=allocations if payload.split_type == "amounts" else {},
        split_parts=payload.split_parts if payload.split_type == "parts" else {},
        to_user_id=payload.to_user_id,
        category=category,
        description=payload.description.strip() if payload.description else None,
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
    split_members = list(dict.fromkeys(updates.get("split_between", transaction.split_between) or group.member_ids))
    if any(member_id not in group.member_ids for member_id in split_members):
        raise HTTPException(status_code=400, detail="Every split member must belong to the group")
    split_type = updates.get("split_type", transaction.split_type)
    split_amounts = updates.get("split_amounts", transaction.split_amounts)
    split_parts = updates.get("split_parts", transaction.split_parts)
    amount = updates.get("amount", transaction.amount)
    try:
        allocations = calculate_split_allocations(amount, split_members, split_type, split_amounts, split_parts)
    except (ValueError, ArithmeticError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    updates.update({
        "split_between": split_members,
        "split_type": split_type,
        "split_amounts": allocations if split_type == "amounts" else {},
        "split_parts": split_parts if split_type == "parts" else {},
    })
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
