import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from books.models import Book
from bookshop.factories import BookFactory, CategoryFactory


# A freshly created book should stringify (and repr) to its own title,
# confirming __str__/__repr__ — and the translation-wrapping
# __getattribute__ override — don't corrupt the original text when no
# translation entry exists for it.
@pytest.mark.django_db
def test_book_str_and_repr_return_title():
    book = BookFactory(title="Кобзар")
    assert str(book) == "Кобзар"
    assert repr(book) == "Кобзар"


# `price` is declared with validators=[MinValueValidator(Decimal('0.01'))].
# Validators only run via full_clean(), so this test exercises that path
# directly rather than relying on a form to catch it.
@pytest.mark.django_db
def test_book_price_below_minimum_fails_validation():
    book = Book(title="Test Book", author="Test Author", price=Decimal("0.00"), stock=1)
    with pytest.raises(ValidationError):
        book.full_clean()


# A valid, positive price should pass full_clean() cleanly (the mirror
# case of the test above — confirms the validator isn't overly strict).
@pytest.mark.django_db
def test_book_valid_price_passes_validation():
    book = Book(
        title="Test Book", author="Test Author", price=Decimal("19.99"), stock=1
    )
    book.full_clean()  # should not raise


# `stock` has default=0 — a Book created without specifying stock should
# not error out or default to None; it should be exactly 0 (out of stock).
@pytest.mark.django_db
def test_book_stock_defaults_to_zero():
    book = Book.objects.create(
        title="No Stock Book", author="Someone", price=Decimal("10.00")
    )
    assert book.stock == 0


# Verifies the ManyToMany relationship between Book and Category works in
# both directions: book.category.all() and category.books.all() (the
# related_name declared on the field).
@pytest.mark.django_db
def test_book_category_relationship_is_bidirectional():
    category = CategoryFactory(name="Фентезі")
    book = BookFactory(category=[category])
    assert category in book.category.all()
    assert book in category.books.all()


# Deleting a Category must NOT delete the books assigned to it — only the
# relation should disappear, since `category` is a ManyToManyField. This
# is the exact behavior promised to users in category_confirm_delete.html
# ("Самі книги видалені не будуть").
@pytest.mark.django_db
def test_deleting_category_does_not_delete_associated_books():
    category = CategoryFactory()
    book = BookFactory(category=[category])
    book_id = book.id

    category.delete()

    assert Book.objects.filter(pk=book_id).exists() is True
    assert Book.objects.get(pk=book_id).category.count() == 0


# Meta.ordering = ['title'] — a default queryset should always come back
# alphabetically sorted, regardless of the order books were created in.
@pytest.mark.django_db
def test_books_are_ordered_by_title_by_default():
    BookFactory(title="Зоряні війни")
    BookFactory(title="Азбука")
    BookFactory(title="Йосип")

    titles = list(Book.objects.values_list("title", flat=True))
    assert titles == sorted(titles)
