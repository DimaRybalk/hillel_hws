from django.contrib import admin
from .models import Order,OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user','total_price','status','created_at')
    list_filter = ('id','user','status','total_price')
    search_fields = ('id','user','status','total_price')
    inlines = [OrderItemInline]
    readonly_fields = ['total_price']

