import asyncio
from unittest.mock import AsyncMock, Mock, patch

from app.models import GroupRead, TransactionCreate, UserRead
from app.routes.expenses import create_group_transaction
from app.services.llm import EXPENSE_CATEGORIES, categorize_expense


@patch("app.services.llm.get_category_classifier")
def test_categorize_expense_uses_name_description_and_local_category_labels(get_classifier):
    classifier = Mock(return_value={"labels": ["Food & drink", "Other"], "scores": [0.9, 0.1]})
    get_classifier.return_value = classifier

    category = categorize_expense("Dinner with friends", "Pizza and drinks")

    assert category == "Food & drink"
    classifier.assert_called_once_with(
        "Dinner with friends. Description: Pizza and drinks",
        candidate_labels=EXPENSE_CATEGORIES,
        hypothesis_template="This expense is about {}.",
        multi_label=False,
    )


@patch("app.services.llm.get_category_classifier")
def test_categorize_expense_falls_back_to_other_if_local_inference_fails(get_classifier):
    get_classifier.side_effect = RuntimeError("model weights unavailable")

    assert categorize_expense("Unclear expense") == "Other"


@patch("app.routes.expenses.run_in_threadpool", new_callable=AsyncMock)
@patch("app.routes.expenses.create_transaction", new_callable=AsyncMock)
@patch("app.routes.expenses.require_group_member", new_callable=AsyncMock)
def test_create_expense_categorizes_title_and_description_when_category_missing(
    require_member,
    save_transaction,
    infer_category,
):
    group = GroupRead(id="g1", name="Trip", description=None, member_ids=["u1"])
    user = UserRead(id="u1", name="Alex", email="alex@example.com")
    require_member.return_value = group
    infer_category.return_value = "Food & drink"
    save_transaction.side_effect = lambda transaction: transaction
    payload = TransactionCreate(title="Dinner", amount=30, description="Pizza after the concert")

    transaction = asyncio.run(create_group_transaction("g1", payload, user))

    infer_category.assert_awaited_once()
    assert infer_category.await_args.args[1:] == ("Dinner", "Pizza after the concert")
    assert transaction.category == "Food & drink"


@patch("app.routes.expenses.run_in_threadpool", new_callable=AsyncMock)
@patch("app.routes.expenses.create_transaction", new_callable=AsyncMock)
@patch("app.routes.expenses.require_group_member", new_callable=AsyncMock)
def test_create_expense_keeps_user_selected_category(
    require_member,
    save_transaction,
    infer_category,
):
    group = GroupRead(id="g1", name="Trip", description=None, member_ids=["u1"])
    user = UserRead(id="u1", name="Alex", email="alex@example.com")
    require_member.return_value = group
    save_transaction.side_effect = lambda transaction: transaction
    payload = TransactionCreate(title="Dinner", amount=30, category="Dining")

    transaction = asyncio.run(create_group_transaction("g1", payload, user))

    infer_category.assert_not_awaited()
    assert transaction.category == "Dining"