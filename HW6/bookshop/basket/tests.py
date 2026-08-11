import pytest
from django.urls import reverse
from django.test import Client
from books.models import Book
from order.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_add_to_cart():
    book = Book.objects.create(title="Гарри Поттер", price=300.00, stock=5)
    client = Client()
    url = reverse("add_to_cart", kwargs={"book_id": book.id})
    client.post(url, data={"quantity": 1})
    cart = client.session.get("cart", {})
    assert str(book.id) in cart
    assert cart[str(book.id)] == 1


@pytest.mark.django_db
def test_delete_object_from_cart():
    book = Book.objects.create(title="Гарри Поттер", price=300.00, stock=5)
    client = Client()
    url = reverse("add_to_cart", kwargs={"book_id": book.id})
    client.post(url, data={"quantity": 1})
    url_delete = reverse("delete_one_book", kwargs={"book_id": book.id})
    client.post(url_delete)
    cart = client.session.get("cart", {})
    assert str(book.id) not in cart


@pytest.mark.django_db
def test_cart_view():
    book1 = Book.objects.create(title="Гарри Поттер", price=300.00, stock=5)
    book2 = Book.objects.create(title="ОЗ", price=100.00, stock=15)
    client = Client()
    url_book1 = reverse("add_to_cart", kwargs={"book_id": book1.id})
    url_book2 = reverse("add_to_cart", kwargs={"book_id": book2.id})
    client.post(url_book1, data={"quantity": 1})
    client.post(url_book2, data={"quantity": 1})
    view_url = reverse("cart_detail")
    response = client.get(view_url)
    assert response.status_code == 200
    assert "Гарри Поттер" in response.content.decode("utf-8")
    assert "ОЗ" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_add_to_cart_unauthorized():
    client = Client()
    url = reverse("submit_cart")
    response = client.post(url)
    assert response.status_code == 302
    assert "login" in response.url


@pytest.mark.django_db
def test_not_enough_stock():
    book = Book.objects.create(title="Гарри Поттер", price=300.00, stock=1)

    username = "test"
    password = "qwerty12345"
    user = User.objects.create_user(
        email="test@gmail.com", username=username, password=password
    )

    client = Client()
    client.login(username=username, password=password)
    client.post(reverse("add_to_cart", kwargs={"book_id": book.id}))
    book.stock = 0
    book.save()
    url = reverse("submit_cart")
    response = client.post(url)
    assert Order.objects.filter(user=user).count() == 0
    assert response.status_code == 302
