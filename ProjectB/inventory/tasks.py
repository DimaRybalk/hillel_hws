import logging
from datetime import timedelta
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import StockItem, StockMovement

logger = logging.getLogger(__name__)


@shared_task
def release_expired_reservations(exp_time_minutes: int = 20):
    cut_time = timezone.now() - timedelta(minutes=exp_time_minutes)
    expired_reservation = StockItem.objects.filter(
        type=StockMovement.MovementType.RESERVE, created_at__lte=cut_time
    ).select_related("stock_item")

    count = 0
    for move in expired_reservation:
        item = move.stock_item
        if item.reserved_items > 0:
            release_qty = min(move.quantity, item.reserved_items)
            with transaction.atomic():
                item.release_reservation(release_qty)
                StockMovement.objects.create(
                    stock_item=item,
                    type=StockMovement.MovementType.RELEASE,
                    quantity=release_qty,
                    comment=f"Автоматичне зняття резерву по таймауту ({exp_time_minutes} хв). Movement ID: {move.id}",
                    responsible_person=None,
                )
                count += 1
                logger.info(
                    f"Автоматично знято з резерву {release_qty} шт. товару book_id={item.book_id}"
                )

    return f"Оброблено {count} прострочених резервів."
