from django.shortcuts import render
from django.urls import reverse_lazy
from categories.models import Category
from .models import Book
from .forms import BookForm
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from asgiref.sync import sync_to_async
from django.http import Http404
from django.core.cache import cache

"""
Views for the `books` app.
 
Handles the public book catalog: listing with search/filter/pagination,
individual book detail pages, and permission-gated create/update/delete
views for managing the catalog.

"""


async def books_view(request):
    
    category_id = request.GET.get('cat')
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q')

    def get_user_data():
            return {
                'can_add_book': request.user.has_perm('books.add_book')
            }
    user_data = await sync_to_async(get_user_data)()

    cache_key = f"books_view:q={query}:cat={category_id}:page={page_number}:can_add={user_data['can_add_book']}"  

    cached_response = await cache.aget(cache_key)
    if cached_response:
        return cached_response    
    
    queryset = Book.objects.prefetch_related('category').all()  
    if query:
        queryset = queryset.filter(title__icontains=query)

    
    if category_id:
        if category_id.isdigit():
            queryset = queryset.filter(category__id=category_id)
        # Non-numeric / invalid 'cat' values are silently ignored
        # rather than raising a 500 error.

    book_list = []
    async for book in queryset:
        book_list.append(book)

    all_categories = []
    async for category in Category.objects.all():
        all_categories.append(category)

    paginator = Paginator(book_list, 10)
    page_obj = paginator.get_page(page_number)

    

    context = {
        'books': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'all_categories': all_categories,
        'can_add_book': user_data['can_add_book'],
    }

    response =  await sync_to_async(render)(request, 'books/books.html', context)
    await cache.aset(cache_key, response, timeout=900)
    return response

async def one_book_view(request, pk):
    cache_key = f"book_detail:{pk}"

    book = await cache.aget(cache_key)

    if not book:
        try:
            queryset = Book.objects.prefetch_related('category')
            book = await queryset.aget(id=pk)
            await cache.aset(cache_key,book,timeout=3600)        
        except Book.DoesNotExist:
            raise Http404('Book does not exist')

    

    def get_user_data():
        return {
            'can_edit_book': request.user.has_perm('books.update_book'),
            'can_delete_book': request.user.has_perm('books.delete_book')
        }

    user_data = await sync_to_async(get_user_data)()

    context = {
        'book': book,
        'can_edit_book': user_data['can_edit_book'],
        'can_delete_book': user_data['can_delete_book'],
    }

    response = await sync_to_async(render)(request, 'books/book_detail.html', context)
    return response

class CreateBookView(PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_create_form.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.add_book'


class DeleteBookView(PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = 'books/book_delete.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.delete_book'


class UpdateBookView(PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_update_form.html'
    success_url = reverse_lazy('books_list')

    permission_required = 'books.update_book'
