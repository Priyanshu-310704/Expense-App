from rest_framework import viewsets

from .models import CurrencyRate, Expense, Settlement
from .serializers import CurrencyRateSerializer, ExpenseSerializer, SettlementSerializer


class CurrencyRateViewSet(viewsets.ModelViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related("group", "payer", "exchange_rate").prefetch_related("splits__person").all()
    serializer_class = ExpenseSerializer


class SettlementViewSet(viewsets.ModelViewSet):
    queryset = Settlement.objects.select_related("group", "paid_by", "paid_to", "exchange_rate").all()
    serializer_class = SettlementSerializer
