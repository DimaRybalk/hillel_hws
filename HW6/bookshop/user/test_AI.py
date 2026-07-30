import pytest
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from bookshop.factories import UserFactory

User = get_user_model()


# Verifies that a user created through the factory is actually persisted
# to the database and picks up the model's default role ('CUSTOMER').
@pytest.mark.django_db
def test_create_user_with_default_role():
    user = UserFactory()
    assert User.objects.filter(pk=user.pk).exists() is True
    assert user.role == 'CUSTOMER'


# CustomUser doesn't override __str__, so it should fall back to
# AbstractUser's default behaviour, which returns the username.
@pytest.mark.django_db
def test_user_str_representation_returns_username():
    user = UserFactory(username='book_lover_42')
    assert str(user) == 'book_lover_42'


# Confirms the 'ADMIN' role can be explicitly assigned and is actually
# persisted to the database (not silently reset back to the default).
@pytest.mark.django_db
def test_user_can_be_assigned_admin_role():
    user = UserFactory(role='ADMIN')
    user.refresh_from_db()
    assert user.role == 'ADMIN'


# `phone` is declared with blank=True, null=True — a user must be able to
# be created without providing one at all (e.g. during normal registration).
@pytest.mark.django_db
def test_user_can_be_created_without_phone():
    user = UserFactory()
    assert user.phone is None


# Two different users are allowed to both have no phone number, since NULL
# values don't collide against a unique constraint at the database level.
# This documents the expected (non-buggy) path for the `unique=True` field.
@pytest.mark.django_db
def test_multiple_users_without_phone_do_not_collide():
    user1 = UserFactory()
    user2 = UserFactory()
    assert user1.phone is None
    assert user2.phone is None
    assert User.objects.filter(phone__isnull=True).count() >= 2


# `phone` has unique=True on the model — this proves two *different* users
# genuinely cannot share the same non-null phone number.
@pytest.mark.django_db
def test_duplicate_phone_number_raises_integrity_error():
    UserFactory(phone='+380501112233')
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            UserFactory(phone='+380501112233')


# Sanity check that the ROLE_CHOICES default ('CUSTOMER') declared on the
# model is what actually gets applied when a user is created directly via
# the manager (not just via the factory's own conveniences).
@pytest.mark.django_db
def test_role_defaults_to_customer_via_manager():
    user = User.objects.create_user(
        username='plainuser',
        email='plain@example.com',
        password='qwerty12345'
    )
    assert user.role == 'CUSTOMER'


# Two users must not be allowed to share a username — this comes from
# Django's built-in AbstractUser field, but is worth asserting explicitly
# since it's core to how login/authentication identifies accounts.
@pytest.mark.django_db
def test_duplicate_username_raises_integrity_error():
    UserFactory(username='duplicate_name')
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            UserFactory(username='duplicate_name')
