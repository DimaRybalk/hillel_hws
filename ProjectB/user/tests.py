import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from warehouse.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_client(api_client):
    admin = UserFactory(is_staff=True, is_superuser=True)
    api_client.force_authenticate(user=admin)
    return api_client


@pytest.fixture
def auth_client(api_client):
    user = UserFactory(is_staff=False)
    api_client.force_authenticate(user=user)
    return api_client


User = get_user_model()


@pytest.mark.django_db
def test_user_list(auth_client):
    UserFactory.create_batch(5)
    url = reverse("user-list")
    response = auth_client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 6


@pytest.mark.django_db
def test_user_one(auth_client):
    user = UserFactory.create()
    url = reverse("user-detail", args=[user.id])
    response = auth_client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_obtain_access_token(api_client):
    user = User.objects.create_user(username="admin", password="admin12345")
    url = reverse("token_obtain_pair")
    payload = {"username": user.username, "password": "admin12345"}
    response = api_client.post(url, data=payload)

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_obtain_access_token_fail(api_client):
    user = User.objects.create_user(username="admin", password="admin12345")
    url = reverse("token_obtain_pair")
    payload = {"username": user.username, "password": "wrongpass"}
    response = api_client.post(url, data=payload)

    assert response.status_code == 401
