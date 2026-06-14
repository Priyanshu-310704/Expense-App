from datetime import date
from decimal import Decimal

import pytest

from expenses.models import CurrencyRate, Expense
from expenses.services import calculate_splits, convert_to_inr
from groups.models import ExpenseGroup, GroupMembership, Person
from groups.services import active_membership, validate_membership_period


@pytest.mark.django_db
def test_membership_periods_are_time_aware():
    group = ExpenseGroup.objects.create(name="Flat")
    meera = Person.objects.create(display_name="Meera")
    GroupMembership.objects.create(group=group, person=meera, joined_on=date(2026, 2, 1), left_on=date(2026, 3, 31))

    assert active_membership(group, meera, date(2026, 3, 31))
    assert not active_membership(group, meera, date(2026, 4, 2))
    with pytest.raises(Exception):
        validate_membership_period(group, meera, date(2026, 3, 1), date(2026, 4, 1))


@pytest.mark.django_db
def test_currency_conversion_uses_date_effective_rate():
    CurrencyRate.objects.create(currency="USD", effective_date=date(2026, 3, 9), rate_to_inr=Decimal("83.20"))

    amount, rate = convert_to_inr(Decimal("10"), "USD", date(2026, 3, 10))

    assert amount == Decimal("832.00")
    assert rate.rate_to_inr == Decimal("83.20")


def test_split_calculation_supports_assignment_split_types():
    aisha, rohan, dev = object(), object(), object()

    assert sum(calculate_splits(Decimal("100"), Expense.SPLIT_EQUAL, [aisha, rohan]).values()) == Decimal("100.00")
    assert calculate_splits(Decimal("100"), Expense.SPLIT_PERCENTAGE, [aisha, rohan], {aisha: Decimal("25"), rohan: Decimal("75")})[rohan] == Decimal("75.00")
    assert calculate_splits(Decimal("120"), Expense.SPLIT_SHARE, [aisha, rohan, dev], {aisha: Decimal("1"), rohan: Decimal("2"), dev: Decimal("3")})[dev] == Decimal("60.00")
    with pytest.raises(ValueError):
        calculate_splits(Decimal("100"), Expense.SPLIT_PERCENTAGE, [aisha, rohan], {aisha: Decimal("60"), rohan: Decimal("60")})
