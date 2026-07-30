from django.test import Client, TestCase, AsyncClient 
import pytest
from django.urls import reverse
from books.models import Book
from books.forms import BookForm
from categories.models import Category
from bookshop.factories import CategoryFactory,BookFactory,UserFactory
from asgiref.sync import sync_to_async

@pytest.mark.django_db
def test_book_form():
    category1 = CategoryFactory()
    category2 = CategoryFactory()

    form_data = {
        'title': 'Code Complete',
        'author': 'Steve McConnell',
        'price': 450.00,
        'description': 'Great book about software construction.',
        'stock': 10,
        'category': [category1.pk, category2.pk]
    }

    form = BookForm(data=form_data)

    assert form.is_valid() is True
    assert not form.errors

@pytest.mark.django_db
def test_book_form_invalid_data():
    category1 = CategoryFactory()
    category2 = CategoryFactory()

    form_data = {
        'title': '',
        'author': 'Steve McConnell',
        'price': '',
        'description': 'Great book about software construction.',
        'stock': 10,
        'category': [category1.pk, category2.pk]
    }

    form = BookForm(data=form_data)

    assert form.is_valid() is False
    assert 'title' in form.errors
    assert 'price' in form.errors

@pytest.mark.django_db
def test_book_form_invalid_price():
    category1 = CategoryFactory()
    category2 = CategoryFactory()

    form_data = {
        'title': 'testname',
        'author': 'Steve McConnell',
        'price': '-50.00',
        'description': 'Great book about software construction.',
        'stock': 10,
        'category': [category1.pk, category2.pk]
    }

    form = BookForm(data=form_data)

    assert form.is_valid() is False
    assert 'price' in form.errors

@pytest.mark.django_db
def test_delete_book():
    
    book = BookFactory()
    category = book.category.first()

    book.delete()

    assert Category.objects.filter(pk=category.pk).exists() is True
    assert Book.objects.filter(pk=book.pk).exists() is False

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_one_book_view():
    async_client = AsyncClient()
    book = await sync_to_async(BookFactory)() 
    url = reverse('book_detail',kwargs={'pk': book.id})
    response = await async_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_flow_book_search():
    book1 = BookFactory(title="Python Programming Guide")
    book2 = BookFactory()

    client = Client()
    
    search_url = reverse('books_list')
    response = client.get(search_url, data={'q': 'Python'})

    assert response.status_code == 200
    books_in_context = response.context['books']
    assert len(books_in_context) == 1
    assert books_in_context[0].title == book1.title


