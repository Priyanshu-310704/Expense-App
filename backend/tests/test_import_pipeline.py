from io import BytesIO

import pytest

from imports.models import ImportAnomaly, ImportRow
from imports.services import create_import_batch, ensure_seed_data


@pytest.mark.django_db
def test_assignment_csv_detects_required_anomalies():
    ensure_seed_data()
    with open(r"C:\Users\prysh\Downloads\Expenses Export.csv", "rb") as handle:
        upload = BytesIO(handle.read())
    upload.name = "Expenses Export.csv"

    batch = create_import_batch(upload)

    categories = set(batch.anomalies.values_list("category", flat=True))
    assert batch.total_rows == 42
    assert {"duplicate", "near_duplicate", "missing_payer", "settlement_like", "split_inconsistency", "currency_conversion", "inactive_member", "ambiguous_date"}.issubset(categories)
    assert batch.rows.get(row_number=13).chosen_action == ImportRow.ACTION_BLOCKED
    assert batch.anomalies.filter(row_number=14, category="settlement_like", approval_required=True).exists()


@pytest.mark.django_db
def test_importer_never_silently_commits_open_review_rows():
    ensure_seed_data()
    with open(r"C:\Users\prysh\Downloads\Expenses Export.csv", "rb") as handle:
        upload = BytesIO(handle.read())
    upload.name = "Expenses Export.csv"

    batch = create_import_batch(upload)

    assert batch.rows.filter(approval_required=True).exists()
    assert ImportAnomaly.objects.filter(batch=batch, approval_required=True, status=ImportAnomaly.STATUS_OPEN).exists()
