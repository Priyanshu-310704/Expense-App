from datetime import date
from decimal import Decimal

import pytest

from balances.services import group_balances, settlement_suggestions
from expenses.models import Expense, ExpenseSplit, Settlement
from expenses.services import rebuild_expense_ledger, rebuild_settlement_ledger
from groups.models import ExpenseGroup, Person


@pytest.mark.django_db
def test_approved_expense_generates_traceable_balances():
    group = ExpenseGroup.objects.create(name="Test")
    aisha = Person.objects.create(display_name="Aisha")
    rohan = Person.objects.create(display_name="Rohan")
    expense = Expense.objects.create(group=group, date=date(2026, 2, 1), description="Dinner", payer=aisha, original_amount=Decimal("1000"), currency="INR", amount_in_inr=Decimal("1000"), split_type=Expense.SPLIT_EQUAL, status=Expense.STATUS_APPROVED)
    ExpenseSplit.objects.create(expense=expense, person=aisha, amount_in_inr=Decimal("500"))
    ExpenseSplit.objects.create(expense=expense, person=rohan, amount_in_inr=Decimal("500"))

    rebuild_expense_ledger(expense)

    balances = {row["person"]: row["balance"] for row in group_balances(group)}
    assert balances["Aisha"] == Decimal("500")
    assert balances["Rohan"] == Decimal("-500")
    assert settlement_suggestions(group) == [{"from": "Rohan", "to": "Aisha", "amount_in_inr": Decimal("500.00")}]


@pytest.mark.django_db
def test_settlement_is_distinct_from_expense_and_updates_ledger():
    group = ExpenseGroup.objects.create(name="Test")
    rohan = Person.objects.create(display_name="Rohan")
    aisha = Person.objects.create(display_name="Aisha")
    settlement = Settlement.objects.create(group=group, date=date(2026, 2, 25), paid_by=rohan, paid_to=aisha, original_amount=Decimal("500"), currency="INR", amount_in_inr=Decimal("500"))

    rebuild_settlement_ledger(settlement)

    balances = {row["person"]: row["balance"] for row in group_balances(group)}
    assert balances["Rohan"] == Decimal("500")
    assert balances["Aisha"] == Decimal("-500")
