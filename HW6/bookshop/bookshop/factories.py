import factory
from django.contrib.auth import get_user_model
from books.models import Book
from categories.models import Category
from order.models import Order, OrderItem
import random

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user_{n}")

    @classmethod
    def _crete(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "qwerty123")
        user = super()._create(*args, **kwargs)
        user.set_password(password)
        user.save()
        return user


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"test category{n}")


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f"test book{n}")
    author = factory.Sequence(lambda n: f"test author{n}")
    price = factory.LazyFunction(lambda: random.randint(100, 500))
    stock = factory.LazyFunction(lambda: random.randint(3, 10))
    description = factory.Sequence(lambda n: f"test description{n}")

    @factory.post_generation
    def category(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for cat in extracted:
                self.category.add(cat)
        else:
            self.category.add(CategoryFactory())


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = "new"
    total_price = 0.00


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    book = factory.SubFactory(BookFactory)
    quantity = 1
