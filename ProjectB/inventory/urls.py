from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StockItemViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r"items", StockItemViewSet, basename="stock-item")
router.register(r"movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = [
    path("", include(router.urls)),
]
