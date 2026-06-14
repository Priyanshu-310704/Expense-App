from rest_framework import viewsets

from .models import ExpenseGroup, GroupMembership, Person
from .serializers import ExpenseGroupSerializer, MembershipSerializer, PersonSerializer


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.prefetch_related("aliases").all()
    serializer_class = PersonSerializer


class ExpenseGroupViewSet(viewsets.ModelViewSet):
    queryset = ExpenseGroup.objects.all()
    serializer_class = ExpenseGroupSerializer


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.select_related("group", "person").all()
    serializer_class = MembershipSerializer
