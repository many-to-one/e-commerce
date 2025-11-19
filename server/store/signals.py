from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.test import RequestFactory
from django.utils.cache import get_cache_key
from .models import Product
from django.conf import settings


# @receiver(post_save, sender=Product)
# @receiver(post_delete, sender=Product)
# def clear_products_cache(sender, **kwargs):

#     print("**** cache request called ****")
#     cache.clear()

