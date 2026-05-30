from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Покупець'),
        ('ADMIN', 'Адмін')
    ]

    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    role = models.CharField(choices=ROLE_CHOICES,default='CUSTOMER')


