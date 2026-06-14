from django.conf import settings
from django.db import models


class ImportBatch(models.Model):
    STATUS_PARSED = "parsed"
    STATUS_COMMITTED = "committed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [(STATUS_PARSED, "Parsed"), (STATUS_COMMITTED, "Committed"), (STATUS_FAILED, "Failed")]

    group = models.ForeignKey("groups.ExpenseGroup", related_name="import_batches", on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    source_filename = models.CharField(max_length=255)
    file_sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PARSED)
    total_rows = models.PositiveIntegerField(default=0)
    committed_rows = models.PositiveIntegerField(default=0)
    skipped_rows = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ImportRow(models.Model):
    ACTION_READY = "ready"
    ACTION_NEEDS_REVIEW = "needs_review"
    ACTION_BLOCKED = "blocked"
    ACTION_REJECTED = "rejected"
    ACTION_COMMITTED = "committed"
    ACTION_SKIPPED = "skipped"
    ACTION_CHOICES = [
        (ACTION_READY, "Ready"),
        (ACTION_NEEDS_REVIEW, "Needs review"),
        (ACTION_BLOCKED, "Blocked"),
        (ACTION_REJECTED, "Rejected"),
        (ACTION_COMMITTED, "Committed"),
        (ACTION_SKIPPED, "Skipped"),
    ]

    batch = models.ForeignKey(ImportBatch, related_name="rows", on_delete=models.CASCADE)
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField()
    normalized_data = models.JSONField(default=dict)
    chosen_action = models.CharField(max_length=30, choices=ACTION_CHOICES, default=ACTION_READY)
    approval_required = models.BooleanField(default=False)
    parse_error = models.TextField(blank=True)

    class Meta:
        unique_together = [("batch", "row_number")]
        ordering = ["row_number"]
        indexes = [models.Index(fields=["batch", "chosen_action"])]


class ImportAnomaly(models.Model):
    SEVERITY_INFO = "info"
    SEVERITY_WARNING = "warning"
    SEVERITY_ERROR = "error"
    SEVERITY_CHOICES = [(SEVERITY_INFO, "Info"), (SEVERITY_WARNING, "Warning"), (SEVERITY_ERROR, "Error")]

    STATUS_OPEN = "open"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_RESOLVED = "resolved"
    STATUS_CHOICES = [(STATUS_OPEN, "Open"), (STATUS_APPROVED, "Approved"), (STATUS_REJECTED, "Rejected"), (STATUS_RESOLVED, "Resolved")]

    batch = models.ForeignKey(ImportBatch, related_name="anomalies", on_delete=models.CASCADE)
    row = models.ForeignKey(ImportRow, related_name="anomalies", on_delete=models.CASCADE)
    row_number = models.PositiveIntegerField()
    category = models.CharField(max_length=80)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    detected_value = models.TextField(blank=True)
    chosen_action = models.CharField(max_length=120)
    approval_required = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["row_number", "category"]
        indexes = [models.Index(fields=["batch", "row_number"]), models.Index(fields=["category", "severity"])]
