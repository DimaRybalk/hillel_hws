from django.urls import path
# from .views import get_all_categories
from .views import CategoriesView,CategoryCreateView,CategoryDeleteView,OneCategoryView,CategoryUpdateView

urlpatterns = [
    path('all/', CategoriesView.as_view(), name='categories_list'),
    path('<int:pk>/', OneCategoryView.as_view(), name='one_category'),
    path('create/', CategoryCreateView.as_view(), name='category_add'),
    path('<int:pk>/delete/', CategoryDeleteView.as_view(), name ='category_delete'),
    path('<int:pk>/edit/', CategoryUpdateView.as_view(), name ='category_edit'),
]