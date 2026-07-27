from decimal import Decimal

from django.db import models
from categories.models import Category
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

class Book(models.Model):
    title = models.CharField(max_length=100,verbose_name='book title')
    author = models.CharField(max_length=100,verbose_name='author name')
    price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='book price',validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField(blank=True,verbose_name='book description')
    stock = models.PositiveIntegerField(default=0,verbose_name='book stock')
    category = models.ManyToManyField(Category,related_name='books')

    class Meta:
        verbose_name = 'book'
        verbose_name_plural = 'books'
        ordering = ['title']
        
    def __str__(self):
        return str(self.title)
    
    def __repr__(self):
        return str(self.title)
    
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if name in ('title','author') and isinstance(attr,str):
            return _(attr)
        return attr