from typing import List

from app.models import BalanceEntry
from app.store import get_user, get_group, list_transactions


async def calculate_group_balances(group_id: str) -> List[BalanceEntry]:
    group = await get_group(group_id)
    if group is None:
        return []

    balances = {member_id: 0.0 for member_id in group.member_ids}
    transactions = await list_transactions(group_id)

    for transaction in transactions:
        if transaction.transaction_type == "reimbursement":
            if transaction.paid_by in balances:
                balances[transaction.paid_by] += transaction.amount
            if transaction.to_user_id in balances:
                balances[transaction.to_user_id] -= transaction.amount
            continue

        members = transaction.split_between or group.member_ids
        share = transaction.amount / len(members) if members else 0.0
        if transaction.paid_by in balances:
            balances[transaction.paid_by] += transaction.amount
        for member_id in members:
            if member_id in balances:
                balances[member_id] -= share

    result = []
    for member_id in group.member_ids:
        user = await get_user(member_id)
        if user:
            result.append(
                BalanceEntry(
                    user_id=user.id,
                    name=user.name,
                    balance=round(balances[member_id], 2),
                )
            )
    return result


async def compute_settlements(group_id: str) -> List[dict]:
    balances = await calculate_group_balances(group_id)
    debtors = [{"user_id": item.user_id, "amount": abs(item.balance)} for item in balances if item.balance < 0]
    creditors = [{"user_id": item.user_id, "amount": item.balance} for item in balances if item.balance > 0]
    settlements = []
    debtor_index = 0
    creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor = debtors[debtor_index]
        creditor = creditors[creditor_index]
        amount = round(min(debtor["amount"], creditor["amount"]), 2)
        if amount:
            settlements.append(
                {
                    "from_user_id": debtor["user_id"],
                    "to_user_id": creditor["user_id"],
                    "amount": amount,
                }
            )
        debtor["amount"] -= amount
        creditor["amount"] -= amount
        if debtor["amount"] <= 0.005:
            debtor_index += 1
        if creditor["amount"] <= 0.005:
            creditor_index += 1

    return settlements
