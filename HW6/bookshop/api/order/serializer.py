from rest_framework import serializers

from api.books.serializer import BookSerializer
from books.models import Book
from order.models import Order,OrderItem



class OrderItemSerializer(serializers.ModelSerializer):

    book = BookSerializer(read_only= True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book',
        write_only=True
    )

    class Meta():
        model = OrderItem
        fields = ['id', 'book','book_id', 'quantity', 'price']
        read_only_fields = ['price']

        

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True)
    class Meta():
        model = Order
        fields = ['id', 'user', 'created_at', 'status', 'total_price', 'items']
        read_only_fields = ['user', 'created_at', 'total_price', 'status']

    def create(self,validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item in items_data:
            OrderItem.objects.create(order=order,**item)

        return order