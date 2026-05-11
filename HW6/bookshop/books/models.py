from django.db import models
from categories.models import Category

class Book(models.Model):
    title = models.CharField(max_length=100,verbose_name='book title')
    author = models.CharField(max_length=100,verbose_name='author name')
    price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='book price')
    description = models.TextField(blank=True,verbose_name='book description')
    stock = models.PositiveIntegerField(default=0,verbose_name='book stock')
    category = models.ManyToManyField(Category,related_name='books')

    class Meta:
        verbose_name = 'book'
        verbose_name_plural = 'books'
        ordering = ['title']
        
    def __str__(self):
        return self.title
    
    def __repr__(self):
        return self.title