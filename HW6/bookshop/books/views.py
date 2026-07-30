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

"""
Views for the `books` app.
 
Handles the public book catalog: listing with search/filter/pagination,
individual book detail pages, and permission-gated create/update/delete
views for managing the catalog.

"""


async def books_view(request):
    queryset = Book.objects.prefetch_related('category').all()

    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(title__icontains=query)

    category_id = request.GET.get('cat')
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
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    def get_user_data():
        return {
            'can_add_book': request.user.has_perm('books.add_book')
        }
    user_data = await sync_to_async(get_user_data)()

    context = {
        'books': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'all_categories': all_categories,
        'can_add_book': user_data['can_add_book'],
    }

    return await sync_to_async(render)(request, 'books/books.html', context)


async def one_book_view(request, pk):
    queryset = Book.objects.prefetch_related('category')

    try:
        book = await queryset.aget(id=pk)
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

    return await sync_to_async(render)(request, 'books/book_detail.html', context)


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
