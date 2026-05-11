
from django.urls import path

from books.views import get_book_by_id, get_books_in_stock


urlpatterns = [
    path('stock_books/',get_books_in_stock),
    path('<book_id>/', get_book_by_id),
]