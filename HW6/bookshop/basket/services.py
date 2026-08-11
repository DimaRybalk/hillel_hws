from books.models import Book
from decimal import Decimal


class SessionCart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get("cart")

        if not cart:
            cart = self.session["cart"] = {}

        self.cart = cart
        self._remove_deleted_books()

    def _remove_deleted_books(self):
        """
        Drop cart entries for books that no longer exist in the database
        (e.g. deleted by an admin) so counts/badges never reference
        phantom items that were removed from the catalog.
        """
        if not self.cart:
            return

        existing_ids = set(
            str(book_id)
            for book_id in Book.objects.filter(id__in=self.cart.keys()).values_list(
                "id", flat=True
            )
        )
        stale_ids = [book_id for book_id in self.cart if book_id not in existing_ids]

        if stale_ids:
            for book_id in stale_ids:
                self.cart.pop(book_id, None)
            self.save()

    def add_to_cart(self, book_id, quantity=1):
        book_id = str(book_id)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return False

        current_quantity = self.cart.get(book_id, 0)
        target_quantity = current_quantity + int(quantity)

        if target_quantity > book.stock:
            if book.stock > 0:
                self.cart[book_id] = book.stock
            else:
                self.cart.pop(book_id, None)

            self.save()
            return False

        self.cart[book_id] = target_quantity
        self.save()
        return True

    def remove_one_from_cart(self, book_id):
        book_id = str(book_id)
        if book_id in self.cart:
            self.cart[book_id] -= 1

            if self.cart[book_id] <= 0:
                self.cart.pop(book_id, None)

            self.save()

    def remove_from_cart(self, book_id):
        book_id = str(book_id)
        if book_id in self.cart:
            self.cart.pop(book_id, None)
            self.save()

    def save(self):
        self.session.modified = True

    def clear_cart(self):
        if "cart" in self.session:
            del self.session["cart"]
            self.save()

    def get_cart_data(self):
        book_ids = self.cart.keys()

        books = Book.objects.filter(id__in=book_ids)
        cart_items = []
        total_price = Decimal(0.00)

        for book in books:
            quantity = self.cart[str(book.id)]
            books_price = book.price * quantity
            total_price += books_price

            cart_items.append(
                {
                    "book": book,
                    "quantity": quantity,
                    "books_price": books_price,
                }
            )

        return {
            "cart_items": cart_items,
            "cart_price": total_price,
        }

    @property
    def total_quantity(self):
        return sum(quantity for quantity in self.cart.values() if quantity > 0)
