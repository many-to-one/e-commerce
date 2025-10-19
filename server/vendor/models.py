from django.db import models
from django.utils.html import mark_safe
from django.utils.text import slugify

from shortuuid.django_fields import ShortUUIDField

from users.models import User


class Vendor(models.Model):
    # user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name="vendor")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor')
    image = models.ImageField(upload_to="vendor", default="shop-image.jpg", blank=True)
    name = models.CharField(max_length=100, help_text="Shop Name", null=True, blank=True)
    nip = models.CharField(max_length=255, help_text="NIP", null=True, blank=True)
    address = models.CharField(max_length=300, help_text="Address", null=True, blank=True)
    marketplace = models.CharField(max_length=100, help_text="Marketplace", null=True, blank=True)
    client_id = models.CharField(max_length=100, help_text="Client_id", null=True, blank=True)
    secret_id = models.CharField(max_length=100, help_text="Secret_id", null=True, blank=True)
    access_token  = models.CharField(max_length=3000, null=True, blank=True)
    reset_token  = models.CharField(max_length=3000, null=True, blank=True)
    email = models.EmailField(max_length=100, help_text="Shop Email", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    mobile = models.CharField(max_length = 150, null=True, blank=True)
    verified = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    vid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefghijklmnopqrstuvxyz")
    date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Vendors"

    def vendor_image(self):
        return mark_safe('  <img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.shop_image.url))

    def __str__(self):
        return str(self.name)
        

    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.name)
        super(Vendor, self).save(*args, **kwargs) 
