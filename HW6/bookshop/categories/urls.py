from django.urls import path
from .views import get_all_categories

urlpatterns = [
    path('all/', get_all_categories, name='categories list')
]