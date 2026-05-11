from django.contrib import admin
from .models import Book

class BookInline(admin.TabularInline):
    model = Book
    extra = 1

@admin.register(Book)
class AdminBook(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'stock')
    list_filter = ('category', 'author')
    search_fields = ('title', 'author', 'description')
