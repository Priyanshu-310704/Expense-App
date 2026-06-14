from decimal import Decimal

from django.db.models import Sum

from expenses.models import LedgerEntry


def group_balances(group):
    rows = LedgerEntry.objects.filter(group=group).values("person", "person__display_name").annotate(balance=Sum("amount_in_inr")).order_by("person__display_name")
    return [{"person_id": row["person"], "person": row["person__display_name"], "balance": row["balance"] or Decimal("0.00")} for row in rows]


def settlement_suggestions(group):
    balances = group_balances(group)
    creditors = [{"person": b["person"], "amount": Decimal(b["balance"])} for b in balances if Decimal(b["balance"]) > 0]
    debtors = [{"person": b["person"], "amount": -Decimal(b["balance"])} for b in balances if Decimal(b["balance"]) < 0]
    suggestions = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        amount = min(debtors[i]["amount"], creditors[j]["amount"]).quantize(Decimal("0.01"))
        if amount > 0:
            suggestions.append({"from": debtors[i]["person"], "to": creditors[j]["person"], "amount_in_inr": amount})
        debtors[i]["amount"] -= amount
        creditors[j]["amount"] -= amount
        if debtors[i]["amount"] <= Decimal("0.00"):
            i += 1
        if creditors[j]["amount"] <= Decimal("0.00"):
            j += 1
    return suggestions


def person_ledger(group, person=None):
    qs = LedgerEntry.objects.filter(group=group).select_related("person", "expense", "settlement").order_by("date", "id")
    if person:
        qs = qs.filter(person=person)
    return qs
