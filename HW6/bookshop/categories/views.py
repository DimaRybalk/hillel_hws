from django.shortcuts import render

from django.db.models import Count
from categories.models import Category

def get_all_categories(request):
    all_categories = Category.objects.annotate(count_books = Count('books'))
    if not all_categories.exists():
        return render(request, 'categories/categories.html', {'error': 'Категорії відсутні', 'all_categories': []})

    return render(request,'categories/categories.html',{'all_categories': all_categories})

