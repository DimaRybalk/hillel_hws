from django.test import TestCase
from django.urls import reverse
from django.test import Client
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from order.models import Order
from books.models import Book
from bookshop.factories import UserFactory

User = get_user_model()

@pytest.mark.django_db
def test_user_registration():
    
    new_user = UserFactory()
    assert User.objects.filter(pk=new_user.pk).exists() is True


@pytest.mark.django_db
def test_user_registration_with_invalid_data():
    client = Client()
    initial_user_count = User.objects.count()
    
    invalid_data = {
        'username': '',
        'email': '',
        'password1': '54321',
        'password2': '54321'
    }

    url = reverse('register') 
    response = client.post(url, data=invalid_data)
    assert User.objects.count() == initial_user_count
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_login():
    new_user = UserFactory()

    client = Client()
    client.force_login(new_user)    
    response_before = client.get(reverse('cart_detail'))
    assert response_before.wsgi_request.user.is_authenticated is True

@pytest.mark.django_db
def test_user_login_with_invalid_data():
    raw_password = 'qwerty12345'
    new_user = UserFactory(password = raw_password)

    client = Client()
    login = client.login(password='123445')    
    assert login is False

@pytest.mark.django_db
def test_user_logout():
    new_user = UserFactory()

    client = Client()
    client.force_login(new_user)
    logout_url = reverse('logout')
    client.post(logout_url)
    response = client.get(reverse('cart_detail'))
    assert response.wsgi_request.user.is_authenticated is False


@pytest.mark.django_db
def test_flow_user_cannot_access_other_user_order():
    user1 = UserFactory()
    user2 = UserFactory()

    order = Order.objects.create(user=user1, total_price=500.00, status='new')
    client = Client()
    client.force_login(user2)
    order_detail_url = reverse('order_detail', kwargs={'pk': order.id})
    response = client.get(order_detail_url)

    assert response.status_code in [403, 404]

@pytest.mark.django_db
def test_flow_user_use_admin_functions():
    user = UserFactory()

    client = Client()
    client.force_login(user)
    book_creation_url = reverse('book_create')
    response = client.get(book_creation_url)

    assert response.status_code in [403, 404]

@pytest.mark.django_db
def test_admin_adds_book():
    admin = UserFactory(is_superuser=True)
    client = Client()
    client.force_login(admin)
    book_creation_url = reverse('book_create')
    response = client.post(book_creation_url)

    assert response.status_code == 200

@pytest.mark.django_db
def test_admin_deletes_book():
    admin = UserFactory(is_superuser=True)
    book = Book.objects.create(title="Django", price=500.00, stock=5)
    client = Client()
    client.force_login(admin)
    book_creation_url = reverse('book_delete',kwargs={'pk': book.id})
    response = client.post(book_creation_url)

    assert response.status_code == 302
    assert Book.objects.filter(pk=book.id).exists() is False