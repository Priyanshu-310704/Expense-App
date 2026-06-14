from django.db import models
from django.db.models import Q


class CurrencyRate(models.Model):
    currency = models.CharField(max_length=3)
    effective_date = models.DateField()
    rate_to_inr = models.DecimalField(max_digits=12, decimal_places=4)
    source = models.CharField(max_length=160, default="manual")
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [("currency", "effective_date")]
        ordering = ["currency", "effective_date"]
        indexes = [models.Index(fields=["currency", "effective_date"])]

    def __str__(self):
        return f"{self.currency} {self.effective_date} = {self.rate_to_inr} INR"


class Expense(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [(STATUS_DRAFT, "Draft"), (STATUS_NEEDS_REVIEW, "Needs review"), (STATUS_APPROVED, "Approved"), (STATUS_REJECTED, "Rejected")]
    SPLIT_EQUAL = "equal"
    SPLIT_UNEQUAL = "unequal"
    SPLIT_PERCENTAGE = "percentage"
    SPLIT_SHARE = "share"
    SPLIT_CHOICES = [(SPLIT_EQUAL, "Equal"), (SPLIT_UNEQUAL, "Unequal"), (SPLIT_PERCENTAGE, "Percentage"), (SPLIT_SHARE, "Share")]

    group = models.ForeignKey("groups.ExpenseGroup", related_name="expenses", on_delete=models.CASCADE)
    date = models.DateField()
    description = models.CharField(max_length=255)
    payer = models.ForeignKey("groups.Person", related_name="paid_expenses", on_delete=models.PROTECT)
    original_amount = models.DecimalField(max_digits=14, decimal_places=4)
    currency = models.CharField(max_length=3)
    amount_in_inr = models.DecimalField(max_digits=14, decimal_places=2)
    exchange_rate = models.ForeignKey(CurrencyRate, null=True, blank=True, on_delete=models.PROTECT)
    split_type = models.CharField(max_length=20, choices=SPLIT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    notes = models.TextField(blank=True)
    import_row = models.OneToOneField("imports.ImportRow", null=True, blank=True, related_name="expense", on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "description"]
        indexes = [models.Index(fields=["group", "date"]), models.Index(fields=["payer", "date"]), models.Index(fields=["status"])]


class ExpenseSplit(models.Model):
    expense = models.ForeignKey(Expense, related_name="splits", on_delete=models.CASCADE)
    person = models.ForeignKey("groups.Person", related_name="expense_splits", on_delete=models.PROTECT)
    amount_in_inr = models.DecimalField(max_digits=14, decimal_places=2)
    raw_value = models.CharField(max_length=80, blank=True)
    membership_valid = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [("expense", "person")]
        indexes = [models.Index(fields=["person"]), models.Index(fields=["expense", "person"])]


class Settlement(models.Model):
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [(STATUS_NEEDS_REVIEW, "Needs review"), (STATUS_APPROVED, "Approved"), (STATUS_REJECTED, "Rejected")]

    group = models.ForeignKey("groups.ExpenseGroup", related_name="settlements", on_delete=models.CASCADE)
    date = models.DateField()
    paid_by = models.ForeignKey("groups.Person", related_name="settlements_paid", on_delete=models.PROTECT)
    paid_to = models.ForeignKey("groups.Person", related_name="settlements_received", on_delete=models.PROTECT)
    original_amount = models.DecimalField(max_digits=14, decimal_places=4)
    currency = models.CharField(max_length=3, default="INR")
    amount_in_inr = models.DecimalField(max_digits=14, decimal_places=2)
    exchange_rate = models.ForeignKey(CurrencyRate, null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_APPROVED)
    notes = models.TextField(blank=True)
    import_row = models.OneToOneField("imports.ImportRow", null=True, blank=True, related_name="settlement", on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["group", "date"]), models.Index(fields=["paid_by", "paid_to"])]
        constraints = [models.CheckConstraint(check=~Q(paid_by=models.F("paid_to")), name="settlement_not_self")]


class LedgerEntry(models.Model):
    KIND_EXPENSE_PAYMENT = "expense_payment"
    KIND_EXPENSE_SHARE = "expense_share"
    KIND_SETTLEMENT_PAID = "settlement_paid"
    KIND_SETTLEMENT_RECEIVED = "settlement_received"
    KIND_CHOICES = [
        (KIND_EXPENSE_PAYMENT, "Expense payment"),
        (KIND_EXPENSE_SHARE, "Expense share"),
        (KIND_SETTLEMENT_PAID, "Settlement paid"),
        (KIND_SETTLEMENT_RECEIVED, "Settlement received"),
    ]

    group = models.ForeignKey("groups.ExpenseGroup", related_name="ledger_entries", on_delete=models.CASCADE)
    person = models.ForeignKey("groups.Person", related_name="ledger_entries", on_delete=models.PROTECT)
    expense = models.ForeignKey(Expense, null=True, blank=True, related_name="ledger_entries", on_delete=models.CASCADE)
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name="ledger_entries", on_delete=models.CASCADE)
    date = models.DateField()
    kind = models.CharField(max_length=40, choices=KIND_CHOICES)
    amount_in_inr = models.DecimalField(max_digits=14, decimal_places=2)
    memo = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "id"]
        indexes = [models.Index(fields=["group", "person"]), models.Index(fields=["group", "date"]), models.Index(fields=["expense"]), models.Index(fields=["settlement"])]
        constraints = [
            models.CheckConstraint(
                check=(Q(expense__isnull=False, settlement__isnull=True) | Q(expense__isnull=True, settlement__isnull=False)),
                name="ledger_has_one_source",
            )
        ]
