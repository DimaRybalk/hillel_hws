from rest_framework import serializers
from .models import StockItem, StockMovement


class ItemSerializer(serializers.ModelSerializer):
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = StockItem
        fields = [
            "id",
            "book_id",
            "quantity",
            "reserved_items",
            "available_quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reserved_items",
            "available_quantity",
            "created_at",
            "updated_at",
        ]


class MovementSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    responsible_person = serializers.CharField(
        source="responsible_person.username", read_only=True
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "stock_item",
            "type",
            "type_display",
            "quantity",
            "comment",
            "responsible_person",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "type_display",
            "responsible_person",
            "created_at",
        ]


class OperationSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, help_text="Кількість книг (≥ 1)")
    comment = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Коментар або ID замовлення",
    )
