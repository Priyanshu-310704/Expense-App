from rest_framework import serializers

from .models import ExpenseGroup, GroupMembership, Person, PersonAlias
from .services import validate_membership_period


class PersonAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonAlias
        fields = ["id", "raw_name", "normalized_name", "person", "confidence", "notes"]


class PersonSerializer(serializers.ModelSerializer):
    aliases = PersonAliasSerializer(many=True, read_only=True)

    class Meta:
        model = Person
        fields = ["id", "display_name", "email", "linked_user", "aliases", "created_at"]
        read_only_fields = ["created_at"]


class ExpenseGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseGroup
        fields = ["id", "name", "base_currency", "created_by", "created_at"]
        read_only_fields = ["created_by", "created_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class MembershipSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source="person.display_name", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = GroupMembership
        fields = ["id", "group", "group_name", "person", "person_name", "joined_on", "left_on", "role", "is_guest", "notes"]

    def validate(self, attrs):
        instance = self.instance
        group = attrs.get("group", getattr(instance, "group", None))
        person = attrs.get("person", getattr(instance, "person", None))
        joined_on = attrs.get("joined_on", getattr(instance, "joined_on", None))
        left_on = attrs.get("left_on", getattr(instance, "left_on", None))
        validate_membership_period(group, person, joined_on, left_on, exclude_id=getattr(instance, "id", None))
        return attrs
