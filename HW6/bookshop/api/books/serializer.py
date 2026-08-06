from rest_framework import serializers
from books.models import Book
from api.categories.serializer import CategorySerializer
from categories.models import Category

class BookSerializer(serializers.ModelSerializer):

    category_details = CategorySerializer(source='category',many=True,read_only=True)

    category = serializers.PrimaryKeyRelatedField(
        queryset = Category.objects.all(),
        many = True,
        write_only = True
    )

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'price', 'description', 'stock', 'category', 'category_details']
        