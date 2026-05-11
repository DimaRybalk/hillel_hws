from django.db import models
from slugify import slugify

class Category(models.Model):
    name = models.CharField(max_length=100,unique=True,verbose_name='categories name')
    slug = models.SlugField(max_length=100,unique=True,verbose_name='category slug')

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['name']

    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args,**kwargs)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name