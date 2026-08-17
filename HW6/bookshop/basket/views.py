from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from books.models import Book
from order.models import Order, OrderItem
from .services import SessionCart
from django.contrib import messages
from silk.profiling.profiler import silk_profile
from django.contrib.auth.mixins import LoginRequiredMixin
import logging
from bookshop.services import WarehouseClient, WarehouseServiceError

"""
Views for the `basket` app.a
Handles the session-based shopping cart: AJAX endpoints for adding,
removing, and decrementing items, rendering the cart detail page, and
converting the cart into a real Order during checkout.
"""

logger = logging.getLogger("order_logger")


class AddToCartView(View):
    def post(self, request, book_id):
        cart = SessionCart(request)

        try:
            quantity = int(request.POST.get("quantity", 1))
            if quantity <= 0:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1
        success = cart.add_to_cart(book_id, quantity=quantity)

        if not success:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Вибачте, більше цієї книги немає на складі!",
                }
            )

        return JsonResponse(
            {
                "status": "success",
                "message": "Книгу додано до кошика!",
                "cart_count": cart.total_quantity,
            }
        )


class DeleteBookFromCartView(View):
    def post(self, request, book_id):
        cart = SessionCart(request)
        cart.remove_from_cart(book_id)
        return JsonResponse({"status": "success", "message": "Книгу видалено!"})


class DeleteOneBookFromCartView(View):
    def post(self, request, book_id):
        cart = SessionCart(request)
        cart.remove_one_from_cart(book_id)
        return JsonResponse({"status": "success"})


class GetCartData(View):
    def get(self, request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()
        cart_data["cart_count"] = cart.total_quantity
        return render(request, "basket/basket_detail.html", context=cart_data)


class SubmitCartView(LoginRequiredMixin, View):

    @silk_profile(name="Оформлення замовлення (Submit Cart)")
    def post(self, request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()

        if not cart_data["cart_items"]:
            messages.error(
                request,
                "Ваш кошик порожній! Додайте книги перед оформленням замовлення.",
            )
            return redirect("cart_detail")

        book_ids = [item["book"].id for item in cart_data["cart_items"]]
        requested_qty = {
            item["book"].id: item["quantity"] for item in cart_data["cart_items"]
        }

        warehouse = WarehouseClient()
        warehouse_reserved = []
        try:
            with transaction.atomic():
                # Lock the relevant book rows for the duration of the transaction
                # to prevent concurrent checkouts from overselling stock.
                locked_books = {
                    book.id: book
                    for book in Book.objects.select_for_update().filter(id__in=book_ids)
                }

                for book_id, quantity in requested_qty.items():
                    book = locked_books.get(book_id)

                    if quantity <= 0:
                        messages.error(
                            request,
                            f"Некоректна кількість для книги '{book.title if book else book_id}'.",
                        )
                        return redirect("cart_detail")

                    if book is None or book.stock < quantity:
                        title = book.title if book else book_id
                        available = book.stock if book else 0
                        messages.error(
                            request,
                            f"Вибачте, книги '{title}' недостатньо на складі. "
                            f"Доступно всього: {available} шт.",
                        )
                        return redirect("cart_detail")

                order = Order.objects.create(
                    user=request.user, total_price=cart_data["cart_price"]
                )

                for book_id, quantity in requested_qty.items():
                    book = locked_books[book_id]
                    book.stock -= quantity
                    book.save()

                    OrderItem.objects.create(
                        order=order, book=book, price=book.price, quantity=quantity
                    )

                    warehouse.reserve_book(
                        book_id=book.id, amount=quantity, order_id=order.id
                    )
                    warehouse_reserved.append((book_id, quantity))

        except WarehouseServiceError as exc:
            logger.error(f"Склад ProjectB недоступний при замовленні: {exc.detail}")
            # Знімаємо вже встановлені резерви на складі ProjectB
            for b_id, qty in warehouse_reserved:
                try:
                    warehouse.release_reservation(
                        book_id=b_id, amount=qty, order_id=order.id
                    )
                except Exception:
                    pass

            messages.error(
                request,
                "Сервіс складу тимчасово недоступний. Спробуйте пізніше.",
            )
            return redirect("cart_detail")

        except Exception as exc:
            logger.error(
                f"Помилка при створенні замовлення або резервуванні: {exc}",
                exc_info=True,
            )
            for b_id, qty in warehouse_reserved:
                try:
                    warehouse.release_reservation(
                        book_id=b_id, amount=qty, order_id=order.id
                    )
                except Exception:
                    pass

            messages.error(
                request,
                "Не вдалося зарезервувати товари на складі. Перевірте залишки.",
            )
            return redirect("cart_detail")

        cart.clear_cart()

        logger.info(
            f"УСПІХ: Користувач {order.user.username} (ID: {order.user.id}) створив замовлення №{order.id} "
            f"на суму {order.total_price} грн. Кількість позицій: {len(cart_data['cart_items'])}"
        )

        return redirect("order_detail", pk=order.id)
