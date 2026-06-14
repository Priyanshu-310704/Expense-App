from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("groups", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="ImportBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_filename", models.CharField(max_length=255)),
                ("file_sha256", models.CharField(max_length=64)),
                ("status", models.CharField(choices=[("parsed", "Parsed"), ("committed", "Committed"), ("failed", "Failed")], default="parsed", max_length=20)),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("committed_rows", models.PositiveIntegerField(default=0)),
                ("skipped_rows", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("group", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="import_batches", to="groups.expensegroup")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ImportRow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("row_number", models.PositiveIntegerField()),
                ("raw_data", models.JSONField()),
                ("normalized_data", models.JSONField(default=dict)),
                ("chosen_action", models.CharField(choices=[("ready", "Ready"), ("needs_review", "Needs review"), ("blocked", "Blocked"), ("rejected", "Rejected"), ("committed", "Committed"), ("skipped", "Skipped")], default="ready", max_length=30)),
                ("approval_required", models.BooleanField(default=False)),
                ("parse_error", models.TextField(blank=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rows", to="imports.importbatch")),
            ],
            options={"ordering": ["row_number"], "unique_together": {("batch", "row_number")}},
        ),
        migrations.CreateModel(
            name="ImportAnomaly",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("row_number", models.PositiveIntegerField()),
                ("category", models.CharField(max_length=80)),
                ("severity", models.CharField(choices=[("info", "Info"), ("warning", "Warning"), ("error", "Error")], max_length=20)),
                ("description", models.TextField()),
                ("detected_value", models.TextField(blank=True)),
                ("chosen_action", models.CharField(max_length=120)),
                ("approval_required", models.BooleanField(default=False)),
                ("status", models.CharField(choices=[("open", "Open"), ("approved", "Approved"), ("rejected", "Rejected"), ("resolved", "Resolved")], default="open", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="anomalies", to="imports.importbatch")),
                ("row", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="anomalies", to="imports.importrow")),
            ],
            options={"ordering": ["row_number", "category"]},
        ),
        migrations.AddIndex(model_name="importrow", index=models.Index(fields=["batch", "chosen_action"], name="imports_imp_batch_i_7b1c42_idx")),
        migrations.AddIndex(model_name="importanomaly", index=models.Index(fields=["batch", "row_number"], name="imports_imp_batch_i_c4d1ef_idx")),
        migrations.AddIndex(model_name="importanomaly", index=models.Index(fields=["category", "severity"], name="imports_imp_categor_242f59_idx")),
    ]
