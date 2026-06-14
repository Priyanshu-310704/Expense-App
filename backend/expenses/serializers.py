from rest_framework import serializers

from .models import CurrencyRate, Expense, ExpenseSplit, LedgerEntry, Settlement
from .services import rebuild_expense_ledger, rebuild_settlement_ledger


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ["id", "currency", "effective_date", "rate_to_inr", "source", "notes"]


class ExpenseSplitSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source="person.display_name", read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = ["id", "expense", "person", "person_name", "amount_in_inr", "raw_value", "membership_valid", "notes"]
        read_only_fields = ["expense"]


class ExpenseSerializer(serializers.ModelSerializer):
    splits = ExpenseSplitSerializer(many=True, required=False)
    payer_name = serializers.CharField(source="payer.display_name", read_only=True)

    class Meta:
        model = Expense
        fields = ["id", "group", "date", "description", "payer", "payer_name", "original_amount", "currency", "amount_in_inr", "exchange_rate", "split_type", "status", "notes", "import_row", "splits", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        splits_data = validated_data.pop("splits", [])
        expense = Expense.objects.create(**validated_data)
        for split in splits_data:
            ExpenseSplit.objects.create(expense=expense, **split)
        rebuild_expense_ledger(expense)
        return expense

    def update(self, instance, validated_data):
        splits_data = validated_data.pop("splits", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if splits_data is not None:
            instance.splits.all().delete()
            for split in splits_data:
                ExpenseSplit.objects.create(expense=instance, **split)
        rebuild_expense_ledger(instance)
        return instance


class SettlementSerializer(serializers.ModelSerializer):
    paid_by_name = serializers.CharField(source="paid_by.display_name", read_only=True)
    paid_to_name = serializers.CharField(source="paid_to.display_name", read_only=True)

    class Meta:
        model = Settlement
        fields = ["id", "group", "date", "paid_by", "paid_by_name", "paid_to", "paid_to_name", "original_amount", "currency", "amount_in_inr", "exchange_rate", "status", "notes", "import_row", "created_at"]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        settlement = super().create(validated_data)
        rebuild_settlement_ledger(settlement)
        return settlement

    def update(self, instance, validated_data):
        settlement = super().update(instance, validated_data)
        rebuild_settlement_ledger(settlement)
        return settlement


class LedgerEntrySerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source="person.display_name", read_only=True)

    class Meta:
        model = LedgerEntry
        fields = ["id", "group", "person", "person_name", "expense", "settlement", "date", "kind", "amount_in_inr", "memo", "created_at"]
