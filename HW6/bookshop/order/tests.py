from .models import Order,OrderItem
from django.contrib.auth import get_user_model
import pytest
from django.urls import reverse
from django.test import Client
from books.models import Book
from unittest.mock import patch, MagicMock
from bookshop.factories import UserFactory,BookFactory,OrderFactory

@pytest.mark.django_db
def test_order_creation_status():
    order = OrderFactory()
    assert order.status == 'new'

@pytest.mark.django_db
def test_flow_successful_order_creation():
    user = UserFactory()
    book = BookFactory()

    client = Client()

    client.force_login(user)
    add_to_cart_url = reverse('add_to_cart',kwargs={'book_id': book.id})
    client.post(add_to_cart_url,data={'quantity': 2})

    submit_cart_url = reverse('submit_cart')
    response = client.post(submit_cart_url)

    assert response.status_code == 302

    order = Order.objects.filter(user=user).first()

    assert order is not None
    assert order.status == 'new'
    assert OrderItem.objects.filter(order=order, book=book, quantity=2).exists() is True

@pytest.mark.django_db
def test_flow_unathorized_user_order():
    client = Client()
    book1 = BookFactory()
    book2 = BookFactory()

    add_to_cart_url1 = reverse('add_to_cart',kwargs={'book_id': book1.id})
    add_to_cart_url2 = reverse('add_to_cart',kwargs={'book_id': book2.id})

    client.post(add_to_cart_url1,data={'quantity': 1})
    client.post(add_to_cart_url2,data={'quantity': 1})

    submit_cart_url = reverse('submit_cart')
    response = client.post(submit_cart_url)

    assert response.status_code == 302
    assert 'login' in response.url

    session = client.session
    assert 'cart' in session
    assert str(book1.id) in session['cart']
    assert str(book2.id) in session['cart']


@pytest.mark.django_db
def test_flow_empty_order_creation():
    user = UserFactory()

    client = Client()

    client.force_login(user)

    submit_cart_url = reverse('submit_cart')
    response = client.post(submit_cart_url)

    assert response.status_code == 302

    assert response.url == reverse('cart_detail')
    assert Order.objects.filter(user=user).exists() is False
    messages = list(response.wsgi_request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Ваш кошик порожній! Додайте книги перед оформленням замовлення."

@pytest.mark.django_db
@patch('payments.views.client')  
def test_flow_successful_payment(mock_stripe_client):
    user = UserFactory()
    book = BookFactory()

    client = Client()
    client.force_login(user)
    
    add_to_cart_url = reverse('add_to_cart', kwargs={'book_id': book.id})
    client.post(add_to_cart_url, data={'quantity': 2})

    submit_cart_url = reverse('submit_cart')
    client.post(submit_cart_url)
    order = Order.objects.filter(user=user).first()
    mock_session = MagicMock()
    mock_session.id = "cs_test_123"
    mock_session.metadata.order_id = order.id
    mock_session.client_reference_id = str(order.id)
    mock_stripe_client.v1.checkout.sessions.retrieve.return_value = mock_session
    checkout_url = reverse('checkout_session')
    client.post(checkout_url)
    successful_payment_url = reverse('payment_success')
    response = client.get(f"{successful_payment_url}?session_id=cs_test_123")
    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == 'paid'


@pytest.mark.django_db
def test_flow_order_total_price_calculation():
    user = UserFactory()
    book1 = BookFactory(price=300.00)
    book2 = BookFactory(price=200.00)

    client = Client()
    client.force_login(user)

    client.post(reverse('add_to_cart', kwargs={'book_id': book1.id}), data={'quantity': 2})
    client.post(reverse('add_to_cart', kwargs={'book_id': book2.id}), data={'quantity': 1})
    client.post(reverse('submit_cart'))
    order = Order.objects.filter(user=user).first()
    assert order.total_price == 800.00
    
@pytest.mark.django_db
def test_flow_cart_cleared_after_order_submission():
    user = UserFactory()
    book = BookFactory()

    client = Client()
    client.force_login(user)

    client.post(reverse('add_to_cart', kwargs={'book_id': book.id}), data={'quantity': 1})
    client.post(reverse('submit_cart'))

    session = client.session
    cart = session.get('cart', {})
    assert len(cart) == 0