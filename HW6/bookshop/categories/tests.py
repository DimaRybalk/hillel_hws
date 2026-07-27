import pytest
from django.urls import reverse
from django.test import AsyncClient,Client
from bookshop.factories import CategoryFactory
from asgiref.sync import sync_to_async
from categories.models import Category

@pytest.mark.django_db
def test_category_slug():
    category = CategoryFactory(name='Детектив')
    assert category.slug == 'detektiv'

@pytest.mark.django_db
def test_str_method():
    category = CategoryFactory(name='Детектив')
    assert str(category) == 'Детектив'

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_one_category_view_success():
    async_client = AsyncClient()
    category = await sync_to_async(CategoryFactory)()
    url = reverse('one_category',kwargs={'pk': category.id})
    response = await async_client.get(url)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_categories_view():
    await sync_to_async(CategoryFactory)(name='Детектив')
    await sync_to_async(CategoryFactory)(name='Фантастика')
    async_client = AsyncClient()
    url = reverse('categories_list')
    response = await async_client.get(url)
    assert response.status_code == 200
    assert 'Детектив' in response.content.decode('utf')
    assert 'Фантастика' in response.content.decode('utf')

@pytest.mark.django_db
def test_create_category_view():
    category = CategoryFactory(name='Детектив')
    assert Category.objects.filter(pk=category.id).exists() is True

@pytest.mark.django_db
def test_delete_category_view():
    category = CategoryFactory(name='Детектив')

    assert Category.objects.count() == 1
    category.delete()   

    assert Category.objects.filter(pk=category.id).exists() is False
    assert Category.objects.count() == 0

@pytest.mark.django_db
def test_flow_user_opens_category():
    category = CategoryFactory(name='Фантастика')
    client = Client()

    list_url = reverse('categories_list')
    response_list = client.get(list_url)
    assert response_list.status_code == 200
    assert 'Фантастика' in response_list.content.decode('utf-8')

    detail_url = reverse('one_category', kwargs={'pk': category.id})
    response_detail = client.get(detail_url)
    assert response_detail.status_code == 200