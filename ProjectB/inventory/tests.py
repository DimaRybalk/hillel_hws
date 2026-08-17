import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from warehouse.factories import ItemFactory,UserFactory

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_user():
    return UserFactory()


@pytest.fixture
def auth_client(api_client, auth_user):
    api_client.force_authenticate(user=auth_user)
    return api_client


@pytest.mark.django_db
def test_list_items(auth_client):
    ItemFactory.create_batch(3)
    url = reverse('stock-item-list')
    response = auth_client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 3

@pytest.mark.django_db
def test_one_item(auth_client):
    item = ItemFactory.create()
    url = reverse('stock-item-detail', args=[item.book_id])
    response = auth_client.get(url)

    assert response.status_code == 200

@pytest.mark.django_db
def test_create_item(auth_client):
    data = {
        "book_id" : 1,
        "quantity" : 30
    }
    url = reverse("stock-item-list")
    response = auth_client.post(url, data=data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["book_id"] == 1
    assert response.data["quantity"] == 30
    assert response.data["reserved_items"] == 0

@pytest.mark.django_db
def test_reserve_api_failure(auth_client):
    item = ItemFactory.create(quantity=5,reserved_items=0)
    url = reverse("stock-item-reserve-stock", args=[item.book_id])
    response = auth_client.post(url, {"amount": 10}, format="json")
    assert response.status_code == 400
    item.refresh_from_db()
    assert item.reserved_items == 0

@pytest.mark.django_db
def test_reserve_api_successful(auth_client):
    item = ItemFactory.create(quantity=5,reserved_items=0)
    url = reverse("stock-item-reserve-stock", args=[item.book_id])
    response = auth_client.post(url, {"amount": 3}, format="json")
    assert response.status_code == 200
    item.refresh_from_db()
    assert item.reserved_items == 3

@pytest.mark.django_db
def test_release_api(auth_client):
    item = ItemFactory.create(quantity=5,reserved_items=3)
    url = reverse("stock-item-release-stock", args=[item.book_id])
    response = auth_client.post(url, {"amount": 2}, format="json")
    assert response.status_code == 200
    item.refresh_from_db()
    assert item.reserved_items == 1

@pytest.mark.django_db
def test_confirm_api(auth_client):
    item = ItemFactory.create(quantity=10,reserved_items = 3)
    url = reverse("stock-item-confirm-sale", args=[item.book_id])
    response = auth_client.post(url, {"amount": 2}, format="json")
    assert response.status_code == 200
    item.refresh_from_db()
    assert item.reserved_items == 1