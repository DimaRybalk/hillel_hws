from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsOwnerOrReadOnly
from order.models import Order
from .serializer import OrderSerializer
from django_filters.rest_framework import DjangoFilterBackend


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "total_price"]

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.prefetch_related("items__book")

        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def perform_create(self, serializer):

        serializer.save(user=self.request.user)
