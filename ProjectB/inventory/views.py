from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from django.core.exceptions import (
    ValidationError,
)
from rest_framework.response import Response

from .models import StockItem, StockMovement
from warehouse.permissions import IsWarehouseStaff, IsWarehouseStaffOrReadOnly
from .serializers import (
    ItemSerializer,
    MovementSerializer,
    OperationSerializer,
)
import logging

logger = logging.getLogger(__name__)


class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.all().order_by("id")
    serializer_class = ItemSerializer
    permission_classes = [IsWarehouseStaffOrReadOnly]
    lookup_field = "book_id"
    filter_backends = [
        filters.OrderingFilter,
    ]

    ordering_fields = ["quantity", "reserved_items", "updated_at"]

    @extend_schema(request=OperationSerializer, responses={200: ItemSerializer})
    @action(detail=True, methods=["post"], url_path="reserve")
    def reserve_stock(self, request, book_id=None):
        item = self.get_object()
        serializer = OperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        comment = serializer.validated_data.get("comment", "")
        try:
            with transaction.atomic():
                item.reserve(amount)
                movement = StockMovement.objects.create(
                    stock_item=item,
                    type=StockMovement.MovementType.RESERVE,
                    quantity=amount,
                    comment=comment,
                    responsible_person=(
                        request.user if request.user.is_authenticated else None
                    ),
                )
                logger.info(
                    f"Операція {movement.type} була створена користувачем {movement.responsible_person} в {movement.created_at}"
                )
                logger.info(
                    f"Товар book_id={item.book_id} зарезервовано на {amount} шт. Користувач: {request.user}"
                )
        except ValidationError as exc:
            logger.warning(
                f"Невдала спроба резервування book_id={item.book_id} (amount={amount}): {exc.messages}"
            )
            return Response({"error": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(
                f"Неочікувана помилка при резервуванні book_id={item.book_id}: {exc}",
                exc_info=True,
            )
            return Response(
                {"error": "Внутрішня помилка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(ItemSerializer(item).data, status=status.HTTP_200_OK)

    @extend_schema(request=OperationSerializer, responses={200: ItemSerializer})
    @action(detail=True, methods=["post"], url_path="release")
    def release_stock(self, request, book_id=None):
        item = self.get_object()
        serializer = OperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        comment = serializer.validated_data.get("comment", "")
        try:
            with transaction.atomic():
                item.release_reservation(amount)
                movement = StockMovement.objects.create(
                    stock_item=item,
                    type=StockMovement.MovementType.RELEASE,
                    quantity=amount,
                    comment=comment,
                    responsible_person=(
                        request.user if request.user.is_authenticated else None
                    ),
                )
                logger.info(
                    f"Операція {movement.type} була створена користувачем {movement.responsible_person} в {movement.created_at}"
                )
                logger.info(
                    f"Товар book_id={item.book_id} знято з резерву на кількість {amount} шт. Користувач: {request.user}"
                )
        except ValidationError as exc:
            logger.warning(
                f"Невдала спроба зняття з резерву book_id={item.book_id} (amount={amount}): {exc.messages}"
            )
            return Response({"error": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(
                f"Неочікувана помилка при знятті з резерву book_id={item.book_id}: {exc}",
                exc_info=True,
            )
            return Response(
                {"error": "Внутрішня помилка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(ItemSerializer(item).data, status=status.HTTP_200_OK)

    @extend_schema(request=OperationSerializer, responses={200: ItemSerializer})
    @action(detail=True, methods=["post"], url_path="confirm-sale")
    def confirm_sale(self, request, book_id=None):
        item = self.get_object()
        serializer = OperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        comment = serializer.validated_data.get("comment", "")
        try:
            with transaction.atomic():
                item.confirm_sale(amount)
                movement = StockMovement.objects.create(
                    stock_item=item,
                    type=StockMovement.MovementType.SALE,
                    quantity=amount,
                    comment=comment,
                    responsible_person=(
                        request.user if request.user.is_authenticated else None
                    ),
                )
                logger.info(
                    f"Операція {movement.type} була створена користувачем {movement.responsible_person} в {movement.created_at}"
                )
                logger.info(
                    f"Підтверджено покупку книги (book_id={item.book_id}) в кількості {amount} шт. Користувач: {request.user}"
                )
        except ValidationError as exc:
            logger.warning(
                f"Помилка при підтвердженні покупки книги (book_id={item.book_id}) Користувач: {request.user}"
            )
            return Response({"error": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(
                f"Неочікувана помилка при підтвердженні book_id={item.book_id}: {exc}",
                exc_info=True,
            )
            return Response(
                {"error": "Внутрішня помилка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(ItemSerializer(item).data, status=status.HTTP_200_OK)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        StockMovement.objects.select_related("stock_item", "responsible_person")
        .all()
        .order_by("-created_at")
    )
    serializer_class = MovementSerializer
    permission_classes = [IsWarehouseStaff]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["type", "stock_item", "responsible_person"]
    ordering_fields = ["created_at", "quantity"]
