# from django.db import models
# from books.models import Book
# from django.contrib.auth.models import User

# from order.models import Order, OrderItem

# class Basket(models.Model):
#     user = models.OneToOneField(User,on_delete=models.CASCADE, related_name='basket')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f'корзина користувача {self.user.username}'

#     def get_basket_cost(self):
#         return sum(item.get_cost() for item in self.items.all())

#     def create_order(self):
#         basket_items = self.items.all()
#         if not basket_items:
#             return None

#         order = Order.objects.create(
#             user = self.user,
#             total_price = self.get_basket_cost()
#         )

#         for basket_item in basket_items:
#             OrderItem.objects.create(
#                 order = order,
#                 book = basket_item.book,
#                 price = basket_item.book.price,
#                 quantity = basket_item.quantity,
#             )

#             basket_item.book.stock -= basket_item.quantity
#             basket_item.book.save()

#         basket_items.delete()

#         return order

# class BasketItem(models.Model):
#     basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name='items')
#     book = models.ForeignKey(Book, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField(default=1)

#     def __str__(self):
#         return f'{self.book.title} x {self.quantity} в кошику'

#     def get_cost(self):
#         return self.book.price*self.quantity
