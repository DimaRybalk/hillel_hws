from django.db import models
from books.models import Book
from user.models import CustomUser


# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = [
        ("new", "Нове"),
        ("paid", "Оплачено"),
        ("sent", "Відправлено"),
        ("cancelled", "Скасовано"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

    def update_total_price(self):
        self.total_price = sum(item.price * item.quantity for item in self.items.all())
        self.save()

    def __str__(self):
        return f"Замовлення №{self.id} на суму {self.total_price}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    quantity = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if not self.price and self.book:
            self.price = self.book.price
        super().save(*args, **kwargs)
        self.order.update_total_price()

    def __str__(self):
        return f"{self.book.title} x {self.quantity} у замовленні №{self.order.id}"
