from django.conf import settings
from django.db import models
from django.db.models import Q


class Person(models.Model):
    display_name = models.CharField(max_length=120, unique=True)
    email = models.EmailField(blank=True)
    linked_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class PersonAlias(models.Model):
    raw_name = models.CharField(max_length=160, unique=True)
    normalized_name = models.CharField(max_length=160, db_index=True)
    person = models.ForeignKey(Person, related_name="aliases", on_delete=models.CASCADE)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["raw_name"]

    def __str__(self):
        return f"{self.raw_name} -> {self.person.display_name}"


class ExpenseGroup(models.Model):
    name = models.CharField(max_length=160)
    base_currency = models.CharField(max_length=3, default="INR")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    ROLE_MEMBER = "member"
    ROLE_GUEST = "guest"
    ROLE_CHOICES = [(ROLE_MEMBER, "Member"), (ROLE_GUEST, "Guest")]

    group = models.ForeignKey(ExpenseGroup, related_name="memberships", on_delete=models.CASCADE)
    person = models.ForeignKey(Person, related_name="memberships", on_delete=models.CASCADE)
    joined_on = models.DateField()
    left_on = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    is_guest = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["joined_on", "person__display_name"]
        indexes = [
            models.Index(fields=["group", "person", "joined_on"]),
            models.Index(fields=["group", "joined_on", "left_on"]),
        ]
        constraints = [
            models.CheckConstraint(check=Q(left_on__isnull=True) | Q(left_on__gte=models.F("joined_on")), name="membership_left_after_join"),
        ]

    def is_active_on(self, date):
        return self.joined_on <= date and (self.left_on is None or date <= self.left_on)

    def __str__(self):
        return f"{self.person} in {self.group}"
