from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class StockItem(models.Model):
    book_id = models.PositiveIntegerField(unique=True, help_text="ID книги")
    quantity = models.PositiveIntegerField(
        default=0, help_text="Залишок книг на складі"
    )
    reserved_items = models.PositiveIntegerField(
        default=0, help_text="Кількість зарезервованих книг"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_quantity(self) -> int:
        return max(0, self.quantity - self.reserved_items)

    def reserve(self, amount: int):
        if amount <= 0:
            raise ValidationError("Кількість зарезервованих книг має бути більшою за 0")
        if amount > self.available_quantity:
            raise ValidationError("Недостатня кількість книг на складі")
        self.reserved_items += amount
        self.save(update_fields=["reserved_items", "updated_at"])

    def release_reservation(self, amount: int):
        if amount <= 0:
            raise ValidationError("Кількість має бути більшою за 0")
        elif amount > self.reserved_items:
            raise ValidationError(
                "Кількість не може бути більша за кількість зарезервованих книг"
            )
        self.reserved_items = max(0, self.reserved_items - amount)
        self.save(update_fields=["reserved_items", "updated_at"])

    def confirm_sale(self, amount: int):
        if amount <= 0:
            raise ValidationError("Кількість має бути більше 0")
        elif self.quantity < amount:
            raise ValidationError("Недостатня кількість книг на складі")
        elif amount > self.reserved_items:
            raise ValidationError(
                f"Неможливо підтвердити продаж: у резерві лише {self.reserved_items} шт., а запитано {amount} шт."
            )
        self.quantity -= amount
        self.reserved_items = max(0, self.reserved_items - amount)
        self.save(update_fields=["quantity", "reserved_items", "updated_at"])

    def __str__(self):
        return f"Book #{self.book_id} (Available: {self.available_quantity})"


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        SUPPLY = "SUPPLY", "Поповнення складу"
        RESERVE = "RESERVE", "Резервування"
        RELEASE = "RELEASE", "Скасування резерву"
        SALE = "SALE", "Списання (Продаж)"

    type = models.CharField(max_length=20, choices=MovementType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    stock_item = models.ForeignKey(
        "StockItem", on_delete=models.CASCADE, related_name="movements"
    )
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField()
    comment = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"[{self.get_type_display()}] Book #{self.stock_item.book_id}: {self.quantity} шт."
