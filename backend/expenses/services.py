from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from .models import CurrencyRate, Expense, ExpenseSplit, LedgerEntry, Settlement

TWOPLACES = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def get_rate(currency, on_date):
    if currency == "INR":
        return None, Decimal("1")
    rate = CurrencyRate.objects.filter(currency=currency, effective_date__lte=on_date).order_by("-effective_date").first()
    if not rate:
        raise ValueError(f"Missing exchange rate for {currency} on {on_date}")
    return rate, Decimal(rate.rate_to_inr)


def convert_to_inr(amount, currency, on_date):
    rate_obj, rate = get_rate(currency, on_date)
    return money(Decimal(amount) * rate), rate_obj


def calculate_splits(total_inr, split_type, participants, detail_values=None):
    total_inr = money(total_inr)
    if not participants:
        raise ValueError("At least one participant is required.")
    detail_values = detail_values or {}
    if split_type == Expense.SPLIT_EQUAL:
        base = money(total_inr / len(participants))
        splits = {person: base for person in participants}
        remainder = total_inr - sum(splits.values(), Decimal("0.00"))
        if remainder:
            splits[participants[0]] = money(splits[participants[0]] + remainder)
        return splits
    if split_type == Expense.SPLIT_UNEQUAL:
        splits = {person: money(detail_values[person]) for person in participants}
        if sum(splits.values(), Decimal("0.00")) != total_inr:
            raise ValueError("Unequal split amounts must equal total amount.")
        return splits
    if split_type == Expense.SPLIT_PERCENTAGE:
        percent_total = sum(Decimal(detail_values[person]) for person in participants)
        if percent_total != Decimal("100"):
            raise ValueError("Percentage split must total 100%.")
        splits = {person: money(total_inr * Decimal(detail_values[person]) / Decimal("100")) for person in participants}
        remainder = total_inr - sum(splits.values(), Decimal("0.00"))
        if remainder:
            splits[participants[0]] = money(splits[participants[0]] + remainder)
        return splits
    if split_type == Expense.SPLIT_SHARE:
        share_total = sum(Decimal(detail_values[person]) for person in participants)
        if share_total <= 0:
            raise ValueError("Share split must have positive total shares.")
        splits = {person: money(total_inr * Decimal(detail_values[person]) / share_total) for person in participants}
        remainder = total_inr - sum(splits.values(), Decimal("0.00"))
        if remainder:
            splits[participants[0]] = money(splits[participants[0]] + remainder)
        return splits
    raise ValueError(f"Unsupported split type {split_type}.")


@transaction.atomic
def rebuild_expense_ledger(expense):
    LedgerEntry.objects.filter(expense=expense).delete()
    if expense.status != Expense.STATUS_APPROVED:
        return
    LedgerEntry.objects.create(group=expense.group, person=expense.payer, expense=expense, date=expense.date, kind=LedgerEntry.KIND_EXPENSE_PAYMENT, amount_in_inr=expense.amount_in_inr, memo=f"Paid: {expense.description}")
    for split in expense.splits.select_related("person"):
        LedgerEntry.objects.create(group=expense.group, person=split.person, expense=expense, date=expense.date, kind=LedgerEntry.KIND_EXPENSE_SHARE, amount_in_inr=-split.amount_in_inr, memo=f"Share: {expense.description}")


@transaction.atomic
def rebuild_settlement_ledger(settlement):
    LedgerEntry.objects.filter(settlement=settlement).delete()
    if settlement.status != Settlement.STATUS_APPROVED:
        return
    LedgerEntry.objects.create(group=settlement.group, person=settlement.paid_by, settlement=settlement, date=settlement.date, kind=LedgerEntry.KIND_SETTLEMENT_PAID, amount_in_inr=settlement.amount_in_inr, memo=f"Settlement paid to {settlement.paid_to.display_name}")
    LedgerEntry.objects.create(group=settlement.group, person=settlement.paid_to, settlement=settlement, date=settlement.date, kind=LedgerEntry.KIND_SETTLEMENT_RECEIVED, amount_in_inr=-settlement.amount_in_inr, memo=f"Settlement received from {settlement.paid_by.display_name}")
