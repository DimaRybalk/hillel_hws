from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Book


@receiver([post_save, post_delete], sender=Book)
def invalidation_book_cache(sender, instance, **kwargs):
    cache_key = f"book_detail:{instance.pk}"
    cache.delete(cache_key)
    print(f"cache #{instance.pk} successfully cleaned")
