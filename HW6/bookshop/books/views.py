from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django import forms
from categories.models import Category
from .models import Book
from django.db.models import Q
from django.views.generic.edit import CreateView,DeleteView,UpdateView
from django.forms import CheckboxSelectMultiple
from django.contrib.auth.mixins import PermissionRequiredMixin
from silk.profiling.profiler import silk_profile
import logging
from django.core.paginator import Paginator
from asgiref.sync import sync_to_async
from django.http import Http404
# ---------------------------- Function-Based Views -----------------------------------------

# def get_all_books(request):
#     all_books = Book.objects.prefetch_related('category').all()
#     if not all_books.exists():
#         return render(request, 'books/books.html', {'error': 'Книги відсутні', 'all_books': []})
    
#     return render(request, 'books/books.html',{'books': all_books})

# def get_books_in_stock(request):
#     stock_books = Book.objects.filter(Q(stock__gt=0))
#     if not stock_books.exists():
#         return render(request, 'books/books.html', {'error': 'Книги відсутні', 'stock_books': []})
#     return render(request, 'books/books.html',{'stock_books': stock_books})
    
# def get_book_by_id(request,book_id):
#     book_by_id = get_object_or_404(Book, id=book_id)
    
#     return render(request, 'books/book_detail.html',{'book_by_id': book_by_id})



# ---------------------------- Class-Based Views -----------------------------------------


logger = logging.getLogger('books_list_logger')

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'price', 'description', 'stock', 'category']
        widgets = {
            'category': forms.CheckboxSelectMultiple(),  
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()


async def books_view(request):
    queryset = Book.objects.prefetch_related('category').all()

    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(title__icontains=query)

    category_id = request.GET.get('cat')
    if category_id:
        queryset = queryset.filter(category__id=category_id)
               
    book_list = [] 
    async for book in queryset:
        book_list.append(book)
    
    all_categories = []
    async for category in Category.objects.all():
        all_categories.append(category)

    paginator = Paginator(book_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    def get_user_data():
        return {
            'cart': request.session.get('cart', {}),
            'can_add_book': request.user.has_perm('books.add_book') 
        }
    user_data = await sync_to_async(get_user_data)()
    cart_count = len(user_data['cart'])

    context = {
        'books': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'all_categories': all_categories,
        'cart_count': cart_count,
        'can_add_book': user_data['can_add_book'],
    }

    return render(request, 'books/books.html', context)
   

async def one_book_view(request,pk):
    queryset = Book.objects.prefetch_related('category')

    try:
        book = await queryset.aget(id=pk)
    except Book.DoesNotExist:
        raise Http404('Book does not exist')
    
    def get_user_data():
        return{
            'cart': request.session.get('cart',{}),
            'can_edit_book': request.user.has_perm('books.edit_book') ,
            'can_delete_book': request.user.has_perm('books.delete_book') 
        }
    
    user_data = await sync_to_async(get_user_data)()
    cart_count = len(user_data['cart'])

    context = {
        'book': book,
        'cart_count': cart_count,
        'can_edit_book': user_data['can_edit_book'],
        'can_delete_book': user_data['can_delete_book'],
    }

    return render(request, 'books/book_detail.html', context)


class CreateBookView(PermissionRequiredMixin,CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_create_form.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.add_book'

class DeleteBookView(PermissionRequiredMixin,DeleteView):
    model = Book
    template_name = 'books/book_delete.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.delete_book'

class UpdateBookView(PermissionRequiredMixin,UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_update_form.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.update_book'