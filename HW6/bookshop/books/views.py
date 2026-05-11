from django.shortcuts import get_object_or_404, render
from .models import Book
from django.db.models import Q

def get_all_books(request):
    all_books = Book.objects.prefetch_related('category').all()
    if not all_books.exists():
        return render(request, 'books/books.html', {'error': 'Книги відсутні', 'all_books': []})
    
    return render(request, 'books/books.html',{'books': all_books})

def get_books_in_stock(request):
    stock_books = Book.objects.filter(Q(stock__gt=0))
    if not stock_books.exists():
        return render(request, 'books/books.html', {'error': 'Книги відсутні', 'stock_books': []})
    return render(request, 'books/books.html',{'stock_books': stock_books})
    
def get_book_by_id(request,book_id):
    book_by_id = get_object_or_404(Book, id=book_id)
    
    return render(request, 'books/book_detail.html',{'book_by_id': book_by_id})
