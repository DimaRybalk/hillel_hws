from django.urls import path
# from .views import get_all_categories
from .views import categories_list_view,CategoryCreateView,CategoryDeleteView,one_category_view,CategoryUpdateView

urlpatterns = [
    path('all/', categories_list_view, name='categories_list'),
    path('<int:pk>/', one_category_view, name='one_category'),
    path('create/', CategoryCreateView.as_view(), name='category_add'),
    path('<int:pk>/delete/', CategoryDeleteView.as_view(), name ='category_delete'),
    path('<int:pk>/edit/', CategoryUpdateView.as_view(), name ='category_edit'),
]