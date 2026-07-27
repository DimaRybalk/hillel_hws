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
    def post(self, request, book_id):
        cart = SessionCart(request)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1
        success = cart.add_to_cart(book_id, quantity=quantity)

        if not success:
            return JsonResponse({
                'status': 'error', 
                'message': 'Вибачте, більше цієї книги немає на складі!'
            })
            
        return JsonResponse({
            'status': 'success',
            'message': 'Книгу додано до кошика!',   
            'cart_count': cart.total_quantity
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
        cart_data['cart_count'] = cart.total_quantity
        return render(request, 'basket/basket_detail.html', context=cart_data)

class SubmitCartView(LoginRequiredMixin,View):

    @silk_profile(name='Оформлення замовлення (Submit Cart)')
    def post(self,request):
        cart = SessionCart(request)
        cart_data = cart.get_cart_data()

        if not cart_data['cart_items']:
            messages.error(request, "Ваш кошик порожній! Додайте книги перед оформленням замовлення.")
            return redirect('cart_detail')

        for item in cart_data['cart_items']:
            book = item['book']

            if item['quantity'] <= 0:
                messages.error(request, f"Некоректна кількість для книги '{book.title}'.")
                return redirect('cart_detail')

            if book.stock < item['quantity']:
                messages.error(
                    request, 
                    f"Вибачте, книги '{book.title}' недостатньо на складі. "
                    f"Доступно всього: {book.stock} шт."
                )
                return redirect('cart_detail')
            
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
