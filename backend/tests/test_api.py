from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_and_import_upload_api():
    user = get_user_model().objects.create_user(username="tester", password="password123")
    client = APIClient()
    client.force_authenticate(user)

    csv = b"date,description,paid_by,amount,currency,split_type,split_with,split_details,notes\n01-02-2026,Rent,Aisha,100,INR,equal,Aisha;Rohan,,\n"
    upload = BytesIO(csv)
    upload.name = "expenses_export.csv"
    response = client.post("/api/imports/", {"file": upload}, format="multipart")

    assert response.status_code == 201
    assert response.data["total_rows"] == 1
