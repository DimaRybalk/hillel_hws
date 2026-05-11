from django.contrib import admin
from .models import Category
from books.admin import BookInline

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list = ['name','slug']
    list_filter = ['name',]
    inline = [BookInline]
    prepopulated_fields = {'slug': ('name',)}
