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




logger = logging.getLogger('order_logger')

class AddToCartView(View):
    def post(self,request,book_id):
        cart = SessionCart(request)
        success = cart.add_to_cart(book_id,quantity=1)
        if not success:
            return JsonResponse({
                'status': 'success', 
                'message': 'Вибачте, більше цієї книги немає на складі!'
            })
            
        return JsonResponse({
            'status': 'success',
            'message': 'Книгу додано до кошика!'
        })
    
class DeleteBookFromCartView(View):
    def post(self,request,book_id):
        cart = SessionCart(request)
        cart.remove_from_cart(book_id)
        return JsonResponse({'status': 'success', 'message': 'Книгу видалено!'})
    
class DeleteOneBookFromCartView(View):
    def post(self,request,book_id):
        cart = SessionCart(request)
        cart.remove_one_from_cart(book_id)
        return JsonResponse({'status': 'success'})
    
class GetCartData(View):
    def get(self,request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()
        return render(request, 'basket/basket_detail.html', context=cart_data)

class SubmitCartView(LoginRequiredMixin,View):

    @silk_profile(name='Оформлення замовлення (Submit Cart)')
    def post(self,request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()

        for item in cart_data['cart_items']:
            book = item['book']
            if book.stock < item['quantity']:
                messages.error(
                    request, 
                    f"Вибачте, книги '{book.title}' недостатньо на складі. "
                    f"Доступно всього: {book.stock} шт."
                )
                return redirect('basket_detail')
            
        order = Order.objects.create(
            user=request.user,
            total_price = cart_data['cart_price']
        )

        for item in cart_data['cart_items']:
            book = item['book']
            book.stock -= item['quantity']
            book.save()

        for item in cart_data['cart_items']:
            OrderItem.objects.create(
                order=order,
                book=item['book'],
                price=item['book'].price,
                quantity=item['quantity']
            )

        cart.clear_cart()

        logger.info(
                    f"УСПІХ: Користувач {order.user.username} (ID: {order.user.id}) створив замовлення №{order.id} "
                    f"на суму {order.total_price} грн. Кількість позицій: {len(cart_data['cart_items'])}"
                )

        return redirect('order_detail', pk=order.id)
