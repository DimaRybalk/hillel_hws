from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        WAREHOUSE_MANAGER = "MANAGER", "Warehouse Manager"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.WAREHOUSE_MANAGER
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
