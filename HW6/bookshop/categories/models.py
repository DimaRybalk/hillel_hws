from django.db import models
from slugify import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=100,unique=True,verbose_name='categories name')
    slug = models.SlugField(max_length=100,unique=True,verbose_name='category slug')

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['name']

    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(str(self.name))
        super().save(*args,**kwargs)

    def __str__(self):
        return str(self.name)
    
    def __repr__(self):
        return str(self.name)
    
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if name == 'name' and isinstance(attr,str):
            return _(attr)
        return attr