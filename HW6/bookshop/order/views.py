# from django.shortcuts import render

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from .models import Order

"""
Views for the `order` app.
 
Handles order history: a paginated list of the logged-in user's past
orders, and a detail page for a single order. Both are strictly
scoped to the requesting user's own orders.
"""


class OrdersListView(LoginRequiredMixin, ListView):
    model = Order
    paginate_by = 10
    template_name = "order/orders.html"
    context_object_name = "orders"

    def get_queryset(self):
        return (
            Order.objects.select_related("user")
            .filter(user=self.request.user)
            .order_by("-id")
        )


class OneOrderView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "order/one_order.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items__book"
        )
