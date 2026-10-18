import pytest

from app.services.expense_service import calculate_split_allocations
from app.models import GroupRead, TransactionRead, UserRead


def test_equal_split_distributes_remainder_in_cents():
    allocations = calculate_split_allocations(10, ["a", "b", "c"])

    assert allocations == {"a": 3.34, "b": 3.33, "c": 3.33}
    assert sum(allocations.values()) == 10


def test_specific_amount_split_requires_exact_total():
    allocations = calculate_split_allocations(
        100,
        ["a", "b"],
        "amounts",
        {"a": 25, "b": 75},
    )

    assert allocations == {"a": 25, "b": 75}
    with pytest.raises(ValueError, match="add up"):
        calculate_split_allocations(100, ["a", "b"], "amounts", {"a": 25, "b": 70})


def test_parts_split_allocates_by_weight():
    allocations = calculate_split_allocations(
        60,
        ["a", "b", "c"],
        "parts",
        split_parts={"a": 1, "b": 2, "c": 3},
    )

    assert allocations == {"a": 10, "b": 20, "c": 30}


def test_split_requires_positive_parts_for_every_selected_member():
    with pytest.raises(ValueError, match="greater than zero"):
        calculate_split_allocations(20, ["a", "b"], "parts", split_parts={"a": 1, "b": 0})


def test_money_values_cannot_exceed_minor_unit_precision():
    with pytest.raises(ValueError, match="up to two decimal places"):
        calculate_split_allocations(10.005, ["a"])
    with pytest.raises(ValueError, match="up to two decimal places"):
        calculate_split_allocations(10, ["a", "b"], "amounts", {"a": 5.001, "b": 4.999})


def test_legacy_documents_default_to_inr_and_equal_split():
    user = UserRead(id="u1", name="Alex", email="alex@example.com")
    group = GroupRead(id="g1", name="Trip", description=None, member_ids=["u1"])
    transaction = TransactionRead(
        id="t1",
        group_id="g1",
        title="Lunch",
        amount=12,
        transaction_type="expense",
        paid_by="u1",
        split_between=["u1"],
    )

    assert user.preferred_currency == "INR"
    assert group.currency == "INR"
    assert transaction.split_type == "equal"
    assert transaction.split_amounts == {}
    assert transaction.split_parts == {}