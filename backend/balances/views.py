from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from expenses.serializers import LedgerEntrySerializer
from groups.models import ExpenseGroup
from .services import group_balances, person_ledger, settlement_suggestions


class BalanceViewSet(viewsets.ViewSet):
    def list(self, request):
        group_id = request.query_params.get("group")
        if not group_id:
            return Response({"detail": "group query parameter is required"}, status=400)
        # Ensure the group belongs to the current user
        try:
            group = ExpenseGroup.objects.get(id=group_id, created_by=request.user)
        except ExpenseGroup.DoesNotExist:
            return Response({"detail": "Group not found."}, status=404)
        return Response({
            "balances": group_balances(group),
            "suggested_settlements": settlement_suggestions(group)
        })

    @action(detail=False, methods=["get"])
    def ledger(self, request):
        group_id = request.query_params.get("group")
        person_id = request.query_params.get("person")
        if not group_id:
            return Response({"detail": "group query parameter is required"}, status=400)
        # Ensure the group belongs to the current user
        try:
            group = ExpenseGroup.objects.get(id=group_id, created_by=request.user)
        except ExpenseGroup.DoesNotExist:
            return Response({"detail": "Group not found."}, status=404)
        return Response(LedgerEntrySerializer(person_ledger(group, person_id), many=True).data)
