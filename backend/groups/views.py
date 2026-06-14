from rest_framework import viewsets

from .models import ExpenseGroup, GroupMembership, Person
from .serializers import ExpenseGroupSerializer, MembershipSerializer, PersonSerializer


class PersonViewSet(viewsets.ModelViewSet):
    serializer_class = PersonSerializer

    def get_queryset(self):
        # Only return people who are members of groups owned by the current user
        user = self.request.user
        user_groups = ExpenseGroup.objects.filter(created_by=user)
        return Person.objects.prefetch_related("aliases").filter(
            memberships__group__in=user_groups
        ).distinct()


class ExpenseGroupViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseGroupSerializer

    def get_queryset(self):
        return ExpenseGroup.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer

    def get_queryset(self):
        user_groups = ExpenseGroup.objects.filter(created_by=self.request.user)
        return GroupMembership.objects.select_related("group", "person").filter(
            group__in=user_groups
        )
