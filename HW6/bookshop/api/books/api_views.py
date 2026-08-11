from books.models import Book
from api.permissions import IsAdminOrReadOnly
from .serializer import BookSerializer
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category"]
    search_fields = ["title", "author"]
