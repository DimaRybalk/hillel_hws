from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django import forms
from categories.models import Category
from .models import Book
from django.db.models import Q
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView,DeleteView,UpdateView
from django.forms import CheckboxSelectMultiple

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


class BooksView(ListView):
    model = Book
    template_name = 'books/books.html'
    paginate_by = 10
    context_object_name = 'books'

    def get_queryset(self):
        queryset = Book.objects.prefetch_related('category').all()
        
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(title__icontains=query)

        category_id = self.request.GET.get('cat')
        if category_id:
            queryset = queryset.filter(category__id=category_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_categories'] = Category.objects.all()
        
        return context

class OneBookView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'

class CreateBookView(CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_create_form.html'
    success_url = reverse_lazy('books_list')

class DeleteBookView(DeleteView):
    model = Book
    template_name = 'books/book_delete.html'
    success_url = reverse_lazy('books_list')

class UpdateBookView(UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_update_form.html'
    success_url = reverse_lazy('books_list')