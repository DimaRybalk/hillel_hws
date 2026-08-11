from django.urls import path

# from books.views import get_book_by_id, get_books_in_stock
from .views import (
    books_view,
    one_book_view,
    CreateBookView,
    DeleteBookView,
    UpdateBookView,
    health_check,
)

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("stock_books/", books_view, name="books_list"),
    path("<int:pk>/detail", one_book_view, name="book_detail"),
    path("create/", CreateBookView.as_view(), name="book_create"),
    path("<int:pk>/delete", DeleteBookView.as_view(), name="book_delete"),
    path("<int:pk>/edit", UpdateBookView.as_view(), name="book_update"),
]
