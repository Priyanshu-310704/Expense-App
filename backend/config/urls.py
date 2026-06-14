from django.contrib import admin
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from balances.views import BalanceViewSet
from expenses.views import CurrencyRateViewSet, ExpenseViewSet, SettlementViewSet
from groups.views import ExpenseGroupViewSet, MembershipViewSet, PersonViewSet
from imports.views import ImportBatchViewSet


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


router = DefaultRouter()
router.register("people", PersonViewSet, basename="person")
router.register("groups", ExpenseGroupViewSet, basename="group")
router.register("memberships", MembershipViewSet, basename="membership")
router.register("currency-rates", CurrencyRateViewSet)
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("settlements", SettlementViewSet, basename="settlement")
router.register("imports", ImportBatchViewSet, basename="importbatch")
router.register("balances", BalanceViewSet, basename="balances")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view()),
    path("api/auth/", include("authentication.urls")),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include(router.urls)),
]
