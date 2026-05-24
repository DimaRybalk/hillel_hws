
from django.urls import path

# from books.views import get_book_by_id, get_books_in_stock
from .views import BooksView,OneBookView,CreateBookView,DeleteBookView,UpdateBookView


urlpatterns = [
    path('stock_books/', BooksView.as_view(), name = 'books_list'),
    path('<int:pk>/detail', OneBookView.as_view(), name = 'book_detail'),
    path('create/',CreateBookView.as_view(),name='book_create'),
    path('<int:pk>/delete',DeleteBookView.as_view(), name='book_delete'),
    path('<int:pk>/edit',UpdateBookView.as_view(), name='book_update'),
]