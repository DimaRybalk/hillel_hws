# from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from .models import Order

class OrdersListView(ListView):
    model = Order
    paginate_by = 10
    template_name = 'order/orders.html'
    context_object_name = 'orders'

    def det_queryset(self):
        return Order.objects.select_related('user').all()

class OneOrderView(DetailView):
    model = Order
    template_name = 'order/one_order.html'
    context_object_name = 'order'        

    def get_queryset(self):
        return Order.objects.prefetch_related('items__book').all()