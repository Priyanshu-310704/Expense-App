from rest_framework import viewsets

from groups.models import ExpenseGroup
from .models import CurrencyRate, Expense, Settlement
from .serializers import CurrencyRateSerializer, ExpenseSerializer, SettlementSerializer


class CurrencyRateViewSet(viewsets.ModelViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user_groups = ExpenseGroup.objects.filter(created_by=self.request.user)
        return Expense.objects.select_related(
            "group", "payer", "exchange_rate"
        ).prefetch_related("splits__person").filter(group__in=user_groups)


class SettlementViewSet(viewsets.ModelViewSet):
    serializer_class = SettlementSerializer

    def get_queryset(self):
        user_groups = ExpenseGroup.objects.filter(created_by=self.request.user)
        return Settlement.objects.select_related(
            "group", "paid_by", "paid_to", "exchange_rate"
        ).filter(group__in=user_groups)
