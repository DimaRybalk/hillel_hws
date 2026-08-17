import factory
from django.contrib.auth import get_user_model
from user.models import CustomUser
from inventory.models import StockMovement, StockItem

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    is_staff = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "default_pass123")
        user = super()._create(model_class, *args, **kwargs)
        user.set_password(password)
        user.save()
        return user


class ItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockItem

    book_id = factory.Sequence(lambda n: n + 1)
    quantity = 50
    reserved_items = 0


class MovementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockMovement

    stock_item = factory.SubFactory(ItemFactory)
    type = StockMovement.MovementType.SUPPLY
    quantity = 50
    responsible_person = factory.SubFactory(UserFactory)
