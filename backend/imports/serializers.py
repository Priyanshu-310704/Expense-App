from rest_framework import serializers

from .models import ImportAnomaly, ImportBatch, ImportRow


class ImportAnomalySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportAnomaly
        fields = ["id", "row", "row_number", "category", "severity", "description", "detected_value", "chosen_action", "approval_required", "status", "created_at"]


class ImportRowSerializer(serializers.ModelSerializer):
    anomalies = ImportAnomalySerializer(many=True, read_only=True)

    class Meta:
        model = ImportRow
        fields = ["id", "row_number", "raw_data", "normalized_data", "chosen_action", "approval_required", "parse_error", "anomalies"]


class ImportBatchSerializer(serializers.ModelSerializer):
    rows = ImportRowSerializer(many=True, read_only=True)
    anomaly_count = serializers.IntegerField(source="anomalies.count", read_only=True)

    class Meta:
        model = ImportBatch
        fields = ["id", "group", "uploaded_by", "source_filename", "file_sha256", "status", "total_rows", "committed_rows", "skipped_rows", "created_at", "anomaly_count", "rows"]
        read_only_fields = ["uploaded_by", "file_sha256", "status", "total_rows", "committed_rows", "skipped_rows", "created_at"]
