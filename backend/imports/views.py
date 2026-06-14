from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from groups.models import ExpenseGroup
from .models import ImportAnomaly, ImportBatch
from .serializers import ImportAnomalySerializer, ImportBatchSerializer
from .services import commit_batch, create_import_batch, import_report, resolve_anomaly


class ImportBatchViewSet(viewsets.ModelViewSet):
    serializer_class = ImportBatchSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user_groups = ExpenseGroup.objects.filter(created_by=self.request.user)
        return ImportBatch.objects.prefetch_related(
            "rows__anomalies", "anomalies"
        ).filter(group__in=user_groups)

    def create(self, request, *args, **kwargs):
        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST)
        batch = create_import_batch(upload, uploaded_by=request.user)
        return Response(self.get_serializer(batch).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def anomalies(self, request, pk=None):
        batch = self.get_object()
        return Response(ImportAnomalySerializer(batch.anomalies.all(), many=True).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        batch = self.get_object()
        anomaly_id = request.data.get("anomaly_id")
        target_status = request.data.get("status", ImportAnomaly.STATUS_APPROVED)
        anomaly = batch.anomalies.get(id=anomaly_id)
        resolve_anomaly(anomaly, target_status)
        return Response(ImportAnomalySerializer(anomaly).data)

    @action(detail=True, methods=["post"])
    def commit(self, request, pk=None):
        batch = commit_batch(self.get_object())
        return Response(import_report(batch))

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        return Response(import_report(self.get_object()))
