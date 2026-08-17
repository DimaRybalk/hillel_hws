from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from warehouse.permissions import IsWarehouseStaff
from .serializers import UserSerializer, UserCreateSerializer
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all().order_by("id")
    permission_classes = [IsWarehouseStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["id", "username", "role"]
    search_fields = ["username", "email"]
    ordering_fields = ["id", "role", "date_joined"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ["list", "create", "destroy"]:
            return [IsWarehouseStaff()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = serializer.save()
        logger.info(
            f"Створення нового користувача '{user.username}' (id={user.id}, role={user.role}) успішне. Створив: {self.request.user}"
        )

    def perform_update(self, serializer):
        old_role = serializer.instance.role
        user = serializer.save()
        if user.role != old_role:
            logger.warning(
                f"Зміна ролі користувача '{user.username}' (id={user.id}): "
                f"'{old_role}' -> '{user.role}'. Змінив: {self.request.user}"
            )
        else:
            logger.info(
                f"Оновлення користувача '{user.username}' (id={user.id}). "
                f"Змінив: {self.request.user}"
            )

    def perform_destroy(self, instance):
        logger.warning(
            f"Видалення користувача '{instance.username}' (id={instance.id}, "
            f"role={instance.role}). Видалив: {self.request.user}"
        )
        instance.delete()
