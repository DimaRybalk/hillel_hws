from django.urls import reverse
import pytest


from bookshop.factories import (
    BookFactory,
    CategoryFactory,
    UserFactory,
    OrderFactory,
    
)
from rest_framework.test import APIClient

# Book


@pytest.mark.django_db
def test_get_books_list():
    api_client = APIClient()
    url = reverse("book-list")
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_single_book_detail():
    book = BookFactory()
    api_client = APIClient()
    url = reverse("book-detail", kwargs={"pk": book.id})
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_create_book_anonymous():
    category = CategoryFactory()
    data = {"title": "Book", "price": "50.00", "stock": 2, "category": category.id}
    api_client = APIClient()
    url = reverse("book-list")
    response = api_client.post(url, data)

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_book_admin():
    admin = UserFactory(is_staff=True, is_superuser=True)
    api_client = APIClient()
    category = CategoryFactory()
    data = {
        "title": "Book",
        "price": "50.00",
        "stock": 2,
        "author": "test",
        "category": [category.id],
    }
    api_client.force_authenticate(user=admin)
    url = reverse("book-list")
    response = api_client.post(url, data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_delete_book_anonymous():
    book = BookFactory()
    api_client = APIClient()

    url = reverse("book-detail", kwargs={"pk": book.id})
    response = api_client.delete(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_delete_book_admin():
    admin = UserFactory(is_staff=True, is_superuser=True)
    book = BookFactory()
    api_client = APIClient()
    api_client.force_authenticate(user=admin)
    url = reverse("book-detail", kwargs={"pk": book.id})
    response = api_client.delete(url)
    assert response.status_code == 204


@pytest.mark.django_db
def test_search_book_by_title():
    book = BookFactory()
    api_client = APIClient()
    url = reverse("book-list")
    response = api_client.get(url, {"search": book.title})

    assert response.status_code == 200


@pytest.mark.django_db
def test_update_book_admin():
    category = CategoryFactory()
    admin = UserFactory(is_staff=True, is_superuser=True)
    book = BookFactory()
    api_client = APIClient()
    api_client.force_authenticate(user=admin)
    data = {
        "title": "New Updated Title",
        "price": "150.00",
        "stock": 10,
        "author": "new",
        "category": [category.id],
    }
    url = reverse("book-detail", kwargs={"pk": book.id})
    response = api_client.put(url, data)
    assert response.status_code == 200

    book.refresh_from_db()
    assert book.title == "New Updated Title"


# Category


@pytest.mark.django_db
def test_category_list():
    api_client = APIClient()
    url = reverse("category-list")
    response = api_client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_category_detail():
    category = CategoryFactory()
    api_client = APIClient()
    url = reverse("category-list")
    response = api_client.get(url, kwargs={"pk": category.id})
    assert response.status_code == 200


@pytest.mark.django_db
def test_category_create_anonymous():
    data = {"name": "Фантастика", "slug": "fantastyka"}
    api_client = APIClient()
    url = reverse("category-list")
    response = api_client.post(url, data)
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_category_admin():
    data = {"name": "Фантастика", "slug": "fantastyka"}
    admin = UserFactory(is_staff=True, is_superuser=True)
    api_client = APIClient()
    api_client.force_authenticate(user=admin)
    url = reverse("category-list")
    response = api_client.post(url, data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_search_category():
    category = CategoryFactory()
    api_client = APIClient()
    url = reverse("category-list")
    response = api_client.get(url, {"search": category.name})

    assert response.status_code == 200


@pytest.mark.django_db
def test_delete_category_anonymous():
    category = CategoryFactory()
    api_client = APIClient()
    url = reverse("category-detail", kwargs={"pk": category.id})
    response = api_client.delete(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_delete_category_admin():
    category = CategoryFactory()
    admin = UserFactory(is_staff=True, is_superuser=True)
    api_client = APIClient()
    api_client.force_authenticate(user=admin)
    url = reverse("category-detail", kwargs={"pk": category.id})
    response = api_client.delete(url)

    assert response.status_code == 204


@pytest.mark.django_db
def test_update_category_admin():
    category = CategoryFactory()
    admin = UserFactory(is_staff=True, is_superuser=True)
    api_client = APIClient()
    api_client.force_authenticate(user=admin)
    url = reverse("category-detail", kwargs={"pk": category.id})
    data = {"name": "Хоррор", "slug": "horror"}
    response = api_client.put(url, data)

    assert response.status_code == 200

    category.refresh_from_db()

    assert category.name == "Хоррор"


@pytest.mark.django_db
def test_update_category_anonymous():
    category = CategoryFactory()
    api_client = APIClient()
    url = reverse("category-detail", kwargs={"pk": category.id})
    data = {"name": "Хоррор", "slug": "horror"}
    response = api_client.put(url, data)

    assert response.status_code == 401


# Order


@pytest.mark.django_db
def test_order_list_authenticated():
    user = UserFactory()
    OrderFactory(user=user)
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    url = reverse("order-list")
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_order_list_anonymous():
    api_client = APIClient()
    url = reverse("order-list")
    response = api_client.get(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_order_detail_owner():
    user = UserFactory()
    order = OrderFactory(user=user)
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    url = reverse("order-detail", kwargs={"pk": order.id})
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_order_detail_other_user_forbidden():
    user1 = UserFactory()
    user2 = UserFactory()
    order = OrderFactory(user=user1)
    api_client = APIClient()
    api_client.force_authenticate(user=user2)
    url = reverse("order-detail", kwargs={"pk": order.id})
    response = api_client.get(url)
    assert response.status_code in [403, 404]


@pytest.mark.django_db
def test_create_order_anonymous():
    book = BookFactory()
    data = {"items": [{"book_id": book.id, "quantity": 2}]}
    api_client = APIClient()
    url = reverse("order-list")
    response = api_client.post(url, data, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_order_authenticated():
    user = UserFactory()
    book = BookFactory()
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    data = {"items": [{"book_id": book.id, "quantity": 1}]}
    url = reverse("order-list")
    response = api_client.post(url, data, format="json")
    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_delete_order_anonymous():
    order = OrderFactory()
    api_client = APIClient()
    url = reverse("order-detail", kwargs={"pk": order.id})
    response = api_client.delete(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_delete_order_admin():
    admin = UserFactory(is_staff=True, is_superuser=True)
    order = OrderFactory(user=admin)
    api_client = APIClient()
    api_client.force_authenticate(user=admin)
    url = reverse("order-detail", kwargs={"pk": order.id})
    response = api_client.delete(url)
    assert response.status_code == 204, response.data
