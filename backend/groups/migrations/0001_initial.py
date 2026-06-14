from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(max_length=120, unique=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("linked_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["display_name"]},
        ),
        migrations.CreateModel(
            name="ExpenseGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("base_currency", models.CharField(default="INR", max_length=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="PersonAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("raw_name", models.CharField(max_length=160, unique=True)),
                ("normalized_name", models.CharField(db_index=True, max_length=160)),
                ("confidence", models.DecimalField(decimal_places=2, default=100, max_digits=5)),
                ("notes", models.TextField(blank=True)),
                ("person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="aliases", to="groups.person")),
            ],
            options={"ordering": ["raw_name"]},
        ),
        migrations.CreateModel(
            name="GroupMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("joined_on", models.DateField()),
                ("left_on", models.DateField(blank=True, null=True)),
                ("role", models.CharField(choices=[("member", "Member"), ("guest", "Guest")], default="member", max_length=20)),
                ("is_guest", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
                ("group", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="groups.expensegroup")),
                ("person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="groups.person")),
            ],
            options={"ordering": ["joined_on", "person__display_name"]},
        ),
        migrations.AddIndex(model_name="expensegroup", index=models.Index(fields=["name"], name="groups_expen_name_5b2f83_idx")),
        migrations.AddIndex(model_name="groupmembership", index=models.Index(fields=["group", "person", "joined_on"], name="groups_group_group_i_6756d9_idx")),
        migrations.AddIndex(model_name="groupmembership", index=models.Index(fields=["group", "joined_on", "left_on"], name="groups_group_group_i_e8cb94_idx")),
        migrations.AddConstraint(model_name="groupmembership", constraint=models.CheckConstraint(check=models.Q(("left_on__isnull", True), ("left_on__gte", models.F("joined_on")), _connector="OR"), name="membership_left_after_join")),
    ]
