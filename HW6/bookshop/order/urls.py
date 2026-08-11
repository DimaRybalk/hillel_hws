from django.urls import path
from .views import OrdersListView, OneOrderView

urlpatterns = [
    path("all/", OrdersListView.as_view(), name="orders_list"),
    path("<int:pk>/", OneOrderView.as_view(), name="order_detail"),
]
