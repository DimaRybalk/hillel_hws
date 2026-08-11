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
from django.http import JsonResponse
from django.db import connection

"""
Views for the `books` app.

Handles the public book catalog: listing with search/filter/pagination,
individual book detail pages, and permission-gated create/update/delete
views for managing the catalog.

"""


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "healthy", "database": "ok"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=503)


async def books_view(request):
    category_id = request.GET.get("cat")
    page_number = request.GET.get("page", 1)
    query = request.GET.get("q")

    def get_user_data():
        return {"can_add_book": request.user.has_perm("books.add_book")}

    user_data = await sync_to_async(get_user_data)()

    data_cache_key = f"books_data:q={query}:cat={category_id}"

    cached_data = await cache.aget(data_cache_key)

    if cached_data:
        book_list = cached_data["book_list"]
        all_categories = cached_data["all_categories"]
    else:
        queryset = Book.objects.prefetch_related("category").all()
        if query:
            queryset = queryset.filter(title__icontains=query)

        if category_id and category_id.isdigit():
            queryset = queryset.filter(category__id=category_id)

        book_list = []
        async for book in queryset:
            book_list.append(book)

        all_categories = []
        async for category in Category.objects.all():
            all_categories.append(category)

        await cache.aset(
            data_cache_key,
            {"book_list": book_list, "all_categories": all_categories},
            timeout=60,
        )

    paginator = Paginator(book_list, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        "books": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "all_categories": all_categories,
        "can_add_book": user_data["can_add_book"],
    }

    return await sync_to_async(render)(request, "books/books.html", context)


async def one_book_view(request, pk):
    cache_key = f"book_detail:{pk}"

    book = await cache.aget(cache_key)

    if not book:
        try:
            queryset = Book.objects.prefetch_related("category")
            book = await queryset.aget(id=pk)
            await cache.aset(cache_key, book, timeout=3600)
        except Book.DoesNotExist:
            raise Http404("Book does not exist")

    def get_user_data():
        return {
            "can_edit_book": request.user.has_perm("books.update_book"),
            "can_delete_book": request.user.has_perm("books.delete_book"),
        }

    user_data = await sync_to_async(get_user_data)()

    context = {
        "book": book,
        "can_edit_book": user_data["can_edit_book"],
        "can_delete_book": user_data["can_delete_book"],
    }

    response = await sync_to_async(render)(request, "books/book_detail.html", context)
    return response


class CreateBookView(PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_create_form.html"
    success_url = reverse_lazy("books_list")

    permission_required = "books.add_book"


class DeleteBookView(PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = "books/book_delete.html"
    success_url = reverse_lazy("books_list")

    permission_required = "books.delete_book"


class UpdateBookView(PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_update_form.html"
    success_url = reverse_lazy("books_list")

    permission_required = "books.update_book"
