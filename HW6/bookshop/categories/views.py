from django.http import Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView,DeleteView,UpdateView
from django.db.models import Count
from categories.models import Category
from books.models import Book
from django.contrib.auth.mixins import PermissionRequiredMixin
from asgiref.sync import sync_to_async
# -------------------------------- Function-Based Views ----------------------------------

# def get_all_categories(request):
#     all_categories = Category.objects.annotate(count_books = Count('books'))
#     if not all_categories.exists():
#         return render(request, 'categories/categories.html', {'error': 'Категорії відсутні', 'all_categories': []})

#     return render(request,'categories/categories.html',{'all_categories': all_categories})



# ------------------------------- Class-Based Views  -------------------------------------

async def categories_list_view(request):
    queryset = Category.objects.annotate(count_books=Count('books', distinct=True)).order_by('name')

    all_categories = []
    async for category in queryset:
        all_categories.append(category)

    def get_user_data():
        return{
            'cart': request.session.get('cart',{}),
            'add': request.user.has_perm('all_categories.add_category'),
            'edit': request.user.has_perm('all_categories.edit_category'),
            'delete': request.user.has_perm('all_categories.delete_category'),
        }
    
    user_data = await sync_to_async(get_user_data)()

    context = {
        'categories': all_categories,
        'can_add': user_data['add'],
        'can_edit': user_data['edit'],
        'can_delete': user_data['delete'],
        'cart_count': len(user_data['cart']),
    }
    return render(request, 'categories/categories.html', context)

class CategoryCreateView(PermissionRequiredMixin,CreateView):
    model = Category
    fields = ['name']
    template_name = 'categories/categories_create_form.html'
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.add_category'


async def one_category_view(request, pk):
    queryset = Category.objects.annotate(count_books=Count('books', distinct=True))
    try:
        category = await queryset.aget(id=pk)
    except Category.DoesNotExist:
        raise Http404("Категорію не знайдено")


    books_queryset = Book.objects.filter(category=category)
    category_books = []
    async for book in books_queryset:
        category_books.append(book)


    def get_user_and_cart():
        user = request.user
        return {
            'cart': request.session.get('cart', {}),
            'is_auth': user.is_authenticated,
            'username': user.email if user.is_authenticated else None,
        }
        
    data = await sync_to_async(get_user_and_cart)()

    context = {
        'category': category,
        'books': category_books,
        'cart_count': len(data['cart']),
        'current_user': {
            'is_authenticated': data['is_auth'],
            'username': data['username'],
        }
    }
    
    return render(request, 'categories/categories_detail.html', context)


class CategoryDeleteView(PermissionRequiredMixin,DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.delete_category'

class CategoryUpdateView(PermissionRequiredMixin,UpdateView):
    model = Category
    template_name = 'categories/categories_update_form.html'
    fields = ['name']
    success_url = reverse_lazy('categories_list')

    permission_required = 'categories.update_category'


