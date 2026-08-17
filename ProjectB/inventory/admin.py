from django.contrib import admin
from .models import StockItem, StockMovement


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = [
        "book_id",
        "quantity",
        "reserved_items",
        "available_quantity",
        "updated_at",
    ]

    search_fields = ("book_id",)
    readonly_fields = ("available_quantity", "created_at", "updated_at")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "stock_item",
        "type",
        "quantity",
        "responsible_person",
        "created_at",
    ]

    list_filter = ("type", "created_at", "responsible_person")
    readonly_fields = ("created_at",)
