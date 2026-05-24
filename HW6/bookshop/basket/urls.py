from django.urls import path
from .views import (
    AddToCartView, 
    DeleteBookFromCartView, 
    DeleteOneBookFromCartView, 
    GetCartData, 
    SubmitCartView
)

urlpatterns = [
    path('add/<int:book_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('delete/<int:book_id>/', DeleteBookFromCartView.as_view(), name='delete_book'),
    path('delete_one_book/<int:book_id>/', DeleteOneBookFromCartView.as_view(), name='delete_one_book'),
    path('detail/', GetCartData.as_view(), name='cart_detail'),
    path('submit/', SubmitCartView.as_view(), name='submit_cart'),
]