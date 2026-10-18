from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from typing import Dict, List, Optional

from app.models import BalanceEntry
from app.store import get_user, get_group, list_transactions


def calculate_split_allocations(
    amount: float,
    members: List[str],
    split_type: str = "equal",
    split_amounts: Optional[Dict[str, float]] = None,
    split_parts: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Return cent-accurate allocations for the selected members."""
    if not members:
        raise ValueError("Select at least one person to split this expense")

    amount_decimal = Decimal(str(amount))
    if amount_decimal != amount_decimal.quantize(Decimal("0.01")):
        raise ValueError("Expense amounts support up to two decimal places")
    total_cents = int((amount_decimal * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if split_type == "amounts":
        allocations = split_amounts or {}
        if set(allocations) != set(members):
            raise ValueError("Enter a specific amount for every selected person")
        decimals = {member_id: Decimal(str(allocations[member_id])) for member_id in members}
        if any(value != value.quantize(Decimal("0.01")) for value in decimals.values()):
            raise ValueError("Specific split amounts support up to two decimal places")
        cents = {member_id: int(value * 100) for member_id, value in decimals.items()}
        if any(value < 0 for value in cents.values()):
            raise ValueError("Split amounts cannot be negative")
        if sum(cents.values()) != total_cents:
            raise ValueError("Specific split amounts must add up to the expense total")
        return {member_id: value / 100 for member_id, value in cents.items()}

    if split_type == "parts":
        weights = split_parts or {}
        if set(weights) != set(members):
            raise ValueError("Enter a share count for every selected person")
        decimal_weights = {member_id: Decimal(str(weights[member_id])) for member_id in members}
        if any(weight <= 0 for weight in decimal_weights.values()):
            raise ValueError("Every share count must be greater than zero")
        total_weight = sum(decimal_weights.values())
    elif split_type == "equal":
        decimal_weights = {member_id: Decimal("1") for member_id in members}
        total_weight = Decimal(len(members))
    else:
        raise ValueError("Unsupported split type")

    raw_cents = {member_id: Decimal(total_cents) * weight / total_weight for member_id, weight in decimal_weights.items()}
    cents = {member_id: int(value.to_integral_value(rounding=ROUND_FLOOR)) for member_id, value in raw_cents.items()}
    remainder = total_cents - sum(cents.values())
    remainder_order = sorted(
        members,
        key=lambda member_id: (raw_cents[member_id] - cents[member_id], -members.index(member_id)),
        reverse=True,
    )
    for member_id in remainder_order[:remainder]:
        cents[member_id] += 1
    return {member_id: value / 100 for member_id, value in cents.items()}


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
        allocations = calculate_split_allocations(
            transaction.amount,
            members,
            transaction.split_type,
            transaction.split_amounts,
            transaction.split_parts,
        )
        if transaction.paid_by in balances:
            balances[transaction.paid_by] += transaction.amount
        for member_id in members:
            if member_id in balances:
                balances[member_id] -= allocations[member_id]

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
