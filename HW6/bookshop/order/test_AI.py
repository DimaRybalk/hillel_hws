import pytest
from decimal import Decimal
from order.models import Order, OrderItem
from bookshop.factories import OrderFactory, UserFactory, BookFactory


# A freshly created order should default to the 'new' status, per
# STATUS_CHOICES / default='new' declared on the model.
@pytest.mark.django_db
def test_order_default_status_is_new():
    order = OrderFactory()
    assert order.status == 'new'


# __str__ should produce a human-readable summary including the order id
# and its current total_price, matching the exact format on the model.
@pytest.mark.django_db
def test_order_str_representation():
    order = OrderFactory(total_price=Decimal('250.00'))
    assert str(order) == f'Замовлення №{order.id} на суму {order.total_price}'


# OrderItem.save() auto-fills `price` from the related book's current
# price when no price is explicitly provided — this exercises that
# fallback branch directly.
@pytest.mark.django_db
def test_orderitem_price_defaults_to_book_price_when_not_provided():
    book = BookFactory(price=Decimal('123.45'))
    order = OrderFactory(total_price=Decimal('0.00'))
    item = OrderItem(order=order, book=book, quantity=2)
    item.save()
    assert item.price == Decimal('123.45')


# An explicitly provided price must NOT be silently overwritten by the
# book's current price — this protects the "price at time of purchase"
# guarantee shown to users on the order detail page (prices can change
# after an order was placed).
@pytest.mark.django_db
def test_orderitem_explicit_price_is_preserved():
    book = BookFactory(price=Decimal('100.00'))
    order = OrderFactory(total_price=Decimal('0.00'))
    item = OrderItem(order=order, book=book, price=Decimal('80.00'), quantity=1)
    item.save()
    assert item.price == Decimal('80.00')


# Saving an OrderItem must trigger Order.update_total_price(), so the
# parent order's total_price always reflects the sum of price * quantity
# across all its items without needing to be updated manually elsewhere.
@pytest.mark.django_db
def test_saving_orderitem_updates_parent_order_total_price():
    order = OrderFactory(total_price=Decimal('0.00'))
    book1 = BookFactory(price=Decimal('50.00'))
    book2 = BookFactory(price=Decimal('30.00'))

    OrderItem.objects.create(order=order, book=book1, quantity=2)  # 100.00
    OrderItem.objects.create(order=order, book=book2, quantity=1)  # 30.00

    order.refresh_from_db()
    assert order.total_price == Decimal('130.00')


# __str__ should include the book title, quantity, and order id, matching
# the documented format on the model.
@pytest.mark.django_db
def test_orderitem_str_representation():
    book = BookFactory(title='Тіні забутих предків')
    order = OrderFactory(total_price=Decimal('0.00'))
    item = OrderItem.objects.create(order=order, book=book, quantity=3)
    assert str(item) == f"{book.title} x 3 у замовленні №{order.id}"


# book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True) —
# deleting the referenced book must NOT delete the historical OrderItem,
# only null out the book reference, preserving order history. This
# matches one_order.html's "Товар видалено з каталогу" fallback text.
@pytest.mark.django_db
def test_deleting_book_sets_orderitem_book_to_null_not_delete():
    book = BookFactory(price=Decimal('45.00'))
    order = OrderFactory(total_price=Decimal('0.00'))
    item = OrderItem.objects.create(order=order, book=book, quantity=1)
    item_id = item.id

    book.delete()

    item.refresh_from_db()
    assert OrderItem.objects.filter(pk=item_id).exists() is True
    assert item.book is None


# Meta.ordering = ['-created_at'] on Order — orders should always come
# back newest-first by default.
@pytest.mark.django_db
def test_orders_are_ordered_newest_first():
    user = UserFactory()
    older = OrderFactory(user=user)
    newer = OrderFactory(user=user)

    orders = list(Order.objects.filter(user=user))
    assert orders[0].pk == newer.pk
    assert orders[-1].pk == older.pk
