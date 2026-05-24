from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView,DeleteView,UpdateView
from django.db.models import Count
from categories.models import Category

# -------------------------------- Function-Based Views ----------------------------------

# def get_all_categories(request):
#     all_categories = Category.objects.annotate(count_books = Count('books'))
#     if not all_categories.exists():
#         return render(request, 'categories/categories.html', {'error': 'Категорії відсутні', 'all_categories': []})

#     return render(request,'categories/categories.html',{'all_categories': all_categories})



# ------------------------------- Class-Based Views  -------------------------------------

class CategoriesView(ListView):
    model = Category
    paginate_by = 10
    template_name = 'categories/categories.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.annotate(count_books=Count('books', distinct=True)).order_by('name')

class CategoryCreateView(CreateView):
    model = Category
    fields = ['name']
    template_name = 'categories/categories_create_form.html'
    success_url = reverse_lazy('categories_list')


class OneCategoryView(DetailView):
    model = Category
    template_name = 'categories/categories_detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return Category.objects.annotate(count_books=Count('books', distinct=True)).order_by('name')


class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('categories_list')


class CategoryUpdateView(UpdateView):
    model = Category
    template_name = 'categories/categories_update_form.html'
    fields = ['name']
    success_url = reverse_lazy('categories_list')


