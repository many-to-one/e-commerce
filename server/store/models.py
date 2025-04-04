from django.db import models
from django.utils.html import mark_safe
from django.utils.text import slugify
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save

from users.models import Profile, User
from vendor.models import Vendor
from shortuuid.django_fields import ShortUUIDField
import shortuuid
import uuid


# Model for Product Categories
class Category(models.Model):

    title = models.CharField(max_length=100)
    category_hierarchy = models.JSONField(null=True, blank=True) 
    allegro_cat_id = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to="category", default="default.jpg", null=True, blank=True)
    active = models.BooleanField(default=True)
    # Slug for SEO-friendly URLs
    slug = models.SlugField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["title"]

    def thumbnail(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.image.url))

    def __str__(self):
        return f'{self.title} - {self.allegro_cat_id}'
    
    # Returns the count of products in this category
    def product_count(self):
        product_count = Product.objects.filter(category=self).count()
        return product_count
    
    # Returns the products in this category
    def cat_products(self):
        cat_products = Product.objects.filter(category=self)
        return cat_products

    # Custom save method to generate a slug if it's empty
    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug is None:
            uuid_key = shortuuid.uuid()
            uniqueid = uuid_key[:4]
            self.slug = slugify(self.title) + "-" + str(uniqueid.lower())
        super(Category, self).save(*args, **kwargs)


class Product(models.Model):

    STATUS = (
        ("draft", "Product is draft"),
        ("disabled", "Product is disabled"),
        ("rejected", "Product is rejected"),
        ("in_review", "Product is in review"),
        ("published", "Product is published"),
    )

    PRODUCT_TYPE = (
        ("regular", "Regular"),
        ("auction", "Auction"),
        ("offer", "Offer")
    )

    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="products", blank=True, null=True, default="default.jpg")
    img_links = models.JSONField(blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="category")
    sub_cat = models.JSONField(null=True, blank=True)
    tags = models.CharField(max_length=1000, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    old_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    stock_qty = models.PositiveIntegerField(default=0)
    in_stock = models.BooleanField(default=True)

    # Product status and type
    status = models.CharField(choices=STATUS, max_length=50, default="published", null=True, blank=True)
    type = models.CharField(choices=PRODUCT_TYPE, max_length=50, default="regular")
    
    # Product flags (featured, hot deal, special offer, digital)
    featured = models.BooleanField(default=False)
    hot_deal = models.BooleanField(default=False)
    special_offer = models.BooleanField(default=False)
    digital = models.BooleanField(default=False)
    
    # Product statistics (views, orders, saved, rating)
    views = models.PositiveIntegerField(default=0, null=True, blank=True)
    orders = models.PositiveIntegerField(default=0, null=True, blank=True)
    saved = models.PositiveIntegerField(default=0, null=True, blank=True)
    rating = models.IntegerField(default=0, null=True, blank=True)

    # Vendor associated with the product
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name="vendor")
    
    # Unique short UUIDs for SKU and product
    sku = models.CharField(max_length=150, null=True, blank=True)
    pid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefghijklmnopqrstuvxyz")
    
    # Slug for SEO-friendly URLs
    slug = models.SlugField(max_length=255, null=True, blank=True,)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-id']
        verbose_name_plural = "Products"

    # Returns an HTML image tag for the product's image
    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.image.url))

    def __str__(self):
        return self.title
    
    # Returns the count of products in the same category as this product
    def category_count(self):
        return Product.objects.filter(category__in=self.category).count()

    def get_precentage(self):
        if self.old_price != 0.00:
            new_price = ((self.old_price - self.price) / self.old_price) * 100
            return round(new_price, 0)
        else:
            return 0
    
    def product_rating(self):
        product_rating = Review.objects.filter(product=self).aggregate(avg_rating=models.Avg('rating'))
        return product_rating['avg_rating']

    def rating_count(self):
        rating_count = Review.objects.filter(product=self).count()
        return rating_count
    
    def gallery(self):
        gallery = Gallery.objects.filter(product=self)
        return gallery
    
    def specification(self):
        return Specification.objects.filter(product=self)

    def specification(self):
        return Specification.objects.filter(product=self)


    def color(self):
        return Color.objects.filter(product=self)
    
    def size(self):
        return Size.objects.filter(product=self)
    

    def save(self, *args, **kwargs):

        uuid_key = shortuuid.uuid()
        uniqueid = uuid_key[:4]
        self.slug = slugify(self.title) + "-" + str(uniqueid.lower())
        super(Product, self).save(*args, **kwargs)

        # if not self.slug or self.slug:
        #     uuid_key = shortuuid.uuid()
        #     uniqueid = uuid_key[:4]
        #     self.slug = slugify(self.title) + "-" + uniqueid.lower()
        
        # if self.stock_qty is not None:
        #     if self.stock_qty == 0:
        #         self.in_stock = False
                
        #     if self.stock_qty > 0:
        #         self.in_stock = True
        # else:
        #     self.stock_qty = 0
        #     self.in_stock = False
        # if self.stock_qty > 0:
        #         self.in_stock = True
        
        # if self.rating > 0:
        #     self.rating = self.product_rating()
            
        # super(Product, self).save(*args, **kwargs) 


class Tag(models.Model):

    title = models.CharField(max_length=30)
    category = models.ForeignKey(Category, default="", verbose_name="Category", on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    slug = models.SlugField("Tag slug", max_length=30, null=False, blank=False, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Tags"
        ordering = ('title',)


class Brand(models.Model):

    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to="products", default="default.jpg", null=True, blank=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Brands"

    def brand_image(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.image.url))

    def __str__(self):
        return self.title


class Gallery(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    image = models.FileField(upload_to="products", default="gallery.jpg")
    active = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    gid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")

    class Meta:
        ordering = ["date"]
        verbose_name_plural = "Product Images"

    def __str__(self):
        return self.product.title


class Specification(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    content = models.CharField(max_length=1000, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Size(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(default=0.00, decimal_places=2, max_digits=12)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Color(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    color_code = models.CharField(max_length=100, blank=True, null=True)
    # image = models.FileField(upload_to=user_directory_path, blank=True, null=True)

    def __str__(self):
        return self.name
    

class Cart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    qty = models.PositiveIntegerField(default=0, null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    sub_total = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    shipping_amount = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    service_fee = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    tax_fee = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    total = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    cart_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    # status = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.cart_id} - {self.product.title}'
    

# Model for Cart Orders
class CartOrder(models.Model):

    PAYMENT_STATUS = (
        ("Zapłacone", "Zapłacone"),
        ("W trakcie", "W trakcie"),
        ("Anulacja", "Anulacja"),
        ("Rozpoczęto", 'Rozpoczęto'),
        ("Wystąpił błąd", 'Wystąpił błąd'),
        ("Zwrot kosztów", 'Zwrot kosztów'),
        ("Nie zapłacone", 'Nie zapłacone'),
        ("Sesja wygasła", 'Sesja wygasła'),
    )


    ORDER_STATUS = (
        ("W trakcie", "W trakcie"),
        ("Czeka na Etykietę", "Czeka na Etykietę"),
        ("Gotowe do wysyłki", "Gotowe do wysyłki"),
        ("Częściowo zakończone", "Częściowo zakończone"),
        ("Anulacja", "Anulacja"),
        
    )

    DELIVERY_STATUS = (
        ("Wstrzymana", "Wstrzymana"),
        ("W trakcie", "W trakcie"),
        ("Czeka na kuriera", "Czeka na kuriera"),
        ("Wysłane", "Wysłane"),
        ("Dostarczono", "Dostarczono"),
        ("W drodze", 'W drodze'),
        ("Wróciło", 'Wróciło'),
        ("Anulacja", 'Anulacja'),
    )

    # vendor = models.ManyToManyField(Vendor, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="buyer", blank=True)
    # product = models.ForeignKey('CartOrderItem', on_delete=models.CASCADE, null=True)
    sub_total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    shipping_amount = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    # VAT (Value Added Tax) cost
    tax_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    # Service fee cost
    service_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    # Total cost of the order
    total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)

    # Order status attributes
    payment_status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default="Rozpoczęto")
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS, default="W trakcie")
    shipping_label = models.FileField(upload_to='shipping_labels/', blank=True, null=True)
    delivery = models.CharField(max_length=100, null=True, blank=True)
    delivery_status = models.CharField(max_length=100, choices=DELIVERY_STATUS, default="W trakcie")
    tracking_id = models.CharField(max_length=100000, null=True, blank=True)
    
    
    # Discounts
    initial_total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="The original total before discounts")
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Amount saved by customer")
    
    # Personal Informations
    full_name = models.CharField(max_length=1000)
    email = models.CharField(max_length=1000)
    mobile = models.CharField(max_length=1000)
    
     # Shipping Address
    street = models.CharField(max_length=1000, null=True, blank=True)
    number = models.CharField(max_length=1000, null=True, blank=True)
    post_code = models.CharField(max_length=1000, null=True, blank=True)
    city = models.CharField(max_length=1000, null=True, blank=True)

    # coupons = models.ManyToManyField('store.Coupon', blank=True)
    
    stripe_session_id = models.CharField(max_length=200,null=True, blank=True)
    # oid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")
    oid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Cart Order"

    def __str__(self):
        return str(self.oid)

    def get_order_items(self):
        return CartOrderItem.objects.filter(order=self)
    
    def get_payment_status_display(self):
        return dict(self.PAYMENT_STATUS).get(self.payment_status, self.payment_status)
    
    def save(self, *args, **kwargs):
        """Automatically update delivery_status when shipping_label is uploaded."""
        if self.shipping_label and self.delivery_status != "Czeka na kuriera":
            self.delivery_status = "Czeka na kuriera"
            self.order_status = "Gotowe do wysyłki"
        super().save(*args, **kwargs)
    

class ReturnItem(models.Model):

    RETURN_STATUS = (
        ("Rozpatrywana", "Rozpatrywana"),
        ("Wstrzymany", "Wstrzymany"),
        ("W procesie", "W procesie"),
        ("Wysłane", "Wysłane"),
        ("Wróciło", "Wróciło"),
        ("W drodze", 'W drodze'),
        ("Anulacja", 'Anulacja'),
    )

    RETURN_REASONS = (
        ("14 Dni: darmowy zwrot", "14 Dni: darmowy zwrot"),
        ("Reklamacja", "Reklamacja"),
        ("Bez powodu", "Bez powodu"),
        ("Brak elementu", "Brak elementu"),
        ("Nie zgodnie z opisem", "Nie zgodnie z opisem"),
    )

    RETURN_DECISIONS = (
        ("Rozpatrywany", "Rozpatrywany"),
        ("Odmowa", "Odmowa"),
        ("Akceptacja", "Akceptacja"),
    )

    RETURN_COSTS = (
        ("Decyzja rozpatrywana", "Decyzja rozpatrywana"),
        ("Darmowy zwrot", "Darmowy zwrot"),
        ("Na własny koszt", "Na własny koszt"),
        ("Na koszt sprzedawcy", "Na koszt sprzedawcy"),
    )


    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    return_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, null=True, blank=True)
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name="returnorder")
    order_item = models.ForeignKey("CartOrderItem", on_delete=models.CASCADE, related_name="returnorderitem", null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="return_item")
    qty = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    date = models.DateTimeField(default=timezone.now)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Estimated Shipping Fee = shipping_fee * total")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Grand Total of all amount listed above")
    return_status = models.CharField(max_length=100, choices=RETURN_STATUS, default="W drodze")
    return_reason = models.CharField(max_length=100, choices=RETURN_REASONS, null=True, blank=True)
    return_decision = models.CharField(max_length=100, choices=RETURN_DECISIONS, default="Rozpatrywany")
    return_costs = models.CharField(max_length=100, choices=RETURN_COSTS, default="Decyzja rozpatrywana")
    return_delivery_courier = models.CharField(max_length=100, null=True, blank=True)
    return_tracking_id = models.CharField(max_length=100000, null=True, blank=True)

    def order_oid(self):
        return self.order.oid
    
    def product_sku(self):
        return self.product.sku
    
    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.product.image.url))


class CartOrderItem(models.Model):

    DELIVERY_STATUS = (
        ("Rozpoczęto", "Rozpoczęto"),
        ("Wstrzymana", "Wstrzymana"),
        ("W trakcie", "W trakcie"),
        ("Wysłane", "Wysłane"),
        ("Dostarczono", "Dostarczono"),
        ("W drodze", 'W drodze'),
        ("Wróciło", 'Wróciło'),
        ("Anulacja", 'Anulacja'),
    )

    RETURN_REASONS = (
        ("14 Dni: darmowy zwrot", "14 Dni: darmowy zwrot"),
        ("Reklamacja", "Reklamacja"),
        ("Bez powodu", "Bez powodu"),
        ("Brak elementu", "Brak elementu"),
        ("Nie zgodnie z opisem", "Nie zgodnie z opisem"),
    )

    RETURN_DECISIONS = (
        ("Rozpatrywany", "Rozpatrywany"),
        ("Odmowa", "Odmowa"),
        ("Akceptacja", "Akceptacja"),
    )

    RETURN_COSTS = (
        ("Decyzja rozpatrywana", "Decyzja rozpatrywana"),
        ("Darmowy zwrot", "Darmowy zwrot"),
        ("Na własny koszt", "Na własny koszt"),
        ("Na koszt sprzedawcy", "Na koszt sprzedawcy"),
    )


    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name="orderitem")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_item")
    allegro_id = models.CharField(max_length=100, null=True, blank=True)
    qty = models.IntegerField(default=0)
    color = models.CharField(max_length=100, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Total of Product price * Product Qty")
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Estimated Shipping Fee = shipping_fee * total")
    tax_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="Estimated Vat based on delivery country = tax_rate * (total + shipping)")
    service_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="Estimated Service Fee = service_fee * total (paid by buyer to platform)")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Grand Total of all amount listed above")
    date = models.DateTimeField(default=timezone.now)
    
    expected_delivery_date_from = models.DateField(auto_now_add=False, null=True, blank=True)
    expected_delivery_date_to = models.DateField(auto_now_add=False, null=True, blank=True)

    initial_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Grand Total of all amount listed above before discount")
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Amount saved by customer")

    # Order stages
    order_placed = models.BooleanField(default=False)
    processing_order = models.BooleanField(default=False)
    quality_check = models.BooleanField(default=False)
    product_shipped = models.BooleanField(default=False)
    product_arrived = models.BooleanField(default=False)
    product_delivered = models.BooleanField(default=False)
    initial_return = models.BooleanField(default=False)
    return_qty = models.IntegerField(null=True, blank=True)
    return_reason = models.CharField(max_length=100, choices=RETURN_REASONS, null=True, blank=True)
    return_decision = models.CharField(max_length=100, choices=RETURN_DECISIONS, default="Rozpatrywany")
    return_costs = models.CharField(max_length=100, choices=RETURN_COSTS, default="Decyzja rozpatrywana")
    return_delivery_courier = models.CharField(max_length=100, null=True, blank=True)
    return_tracking_id = models.CharField(max_length=100000, null=True, blank=True)

    # Various fields for delivery status, delivery couriers, tracking ID, coupons, and more
    delivery_status = models.CharField(max_length=100, choices=DELIVERY_STATUS, default="Rozpoczęto")
    delivery_courier = models.ForeignKey("store.DeliveryCouriers", on_delete=models.SET_NULL, null=True, blank=True)
    tracking_id = models.CharField(max_length=100000, null=True, blank=True)

    def order_oid(self):
        return self.order.oid
    
    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.product.image.url))



    # Model for Product FAQs
class ProductFaq(models.Model):
    # User who asked the FAQ
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # Unique short UUID for FAQ
    pid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefghijklmnopqrstuvxyz")
    # Product associated with the FAQ
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name="product_faq")
    # Email of the user who asked the question
    email = models.EmailField()
    # FAQ question
    question = models.CharField(max_length=1000)
    # FAQ answer
    answer = models.CharField(max_length=10000, null=True, blank=True)
    # Is the FAQ active?
    active = models.BooleanField(default=False)
    # Date of FAQ creation
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Faqs"
        ordering = ["-date"]
        
    def __str__(self):
        return self.question
    

class Review(models.Model):

    RATING = (
        ( 1,  "★☆☆☆☆"),
        ( 2,  "★★☆☆☆"),
        ( 3,  "★★★☆☆"),
        ( 4,  "★★★★☆"),
        ( 5,  "★★★★★"),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviews")
    review = models.TextField()
    reply = models.CharField(null=True, blank=True, max_length=1000)
    rating = models.IntegerField(choices=RATING, default=None)
    active = models.BooleanField(default=False)
    # helpful = models.ManyToManyField(User, blank=True, related_name="helpful")
    # not_helpful = models.ManyToManyField(User, blank=True, related_name="not_helpful")
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Reviews & Rating"
        ordering = ["-date"]
        
    def __str__(self):
        if self.product:
            return self.product.title
        else:
            return "Review"
        
    # Method to get the rating value
    def get_rating(self):
        return self.rating
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
# Signal handler to update the product rating when a review is saved
@receiver(post_save, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    if instance.product:
        instance.product.save()


class Wishlist(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist")
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Wishlist"
    
    def __str__(self):
        if self.product.title:
            return self.product.title
        else:
            return "Wishlist"
        

class Notification(models.Model):

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(CartOrder, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    seen = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Notification"
    
    def __str__(self):
        if self.order:
            return self.order.oid
        else:
            return "Notification"
        

# Define a model for Address
class Address(models.Model):
    # A foreign key relationship to the User model with CASCADE deletion
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # Fields for full name, mobile, email, country, state, town/city, address, zip code, and status
    full_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    # country = models.ForeignKey("addon.Tax", on_delete=models.SET_NULL, null=True, related_name="address_country", blank=True)
    state = models.CharField(max_length=100)
    town_city = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    zip = models.CharField(max_length=100)
    status = models.BooleanField(default=False)
    same_as_billing_address = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Address"
    
    # Method to return a string representation of the object
    def __str__(self):
        if self.user:
            return self.user.username
        else:
            return "Address"


class CancelledOrder(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    orderitem = models.ForeignKey("store.CartOrderItem", on_delete=models.SET_NULL, null=True)
    email = models.CharField(max_length=100)
    refunded = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Cancelled Order"
    
    # Method to return a string representation of the object
    def __str__(self):
        if self.user:
            return str(self.user.username)
        else:
            return "Cancelled Order"


class Coupon(models.Model):

    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, related_name="coupon_vendor")
    used_by = models.ManyToManyField(User, blank=True)
    code = models.CharField(max_length=1000)
    # type = models.CharField(max_length=100, choices=DISCOUNT_TYPE, default="Percentage")
    discount = models.IntegerField(default=1) #validators=[MinValueValidator(0), MaxValueValidator(100)]
    # redemption = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    # make_public = models.BooleanField(default=False)
    # valid_from = models.DateField()
    # valid_to = models.DateField()
    # ShortUUID field
    cid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")
    
    # Method to calculate and save the percentage discount
    def save(self, *args, **kwargs):
        new_discount = int(self.discount) / 100
        self.get_percent = new_discount
        super(Coupon, self).save(*args, **kwargs) 
    
    def __str__(self):
        return self.code
    
    class Meta:
        ordering =['-id']

# # Define a model for Coupon Users
# class CouponUsers(models.Model):
#     # A foreign key relationship to the Coupon model with CASCADE deletion
#     coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
#     # A foreign key relationship to the CartOrder model with CASCADE deletion
#     order = models.ForeignKey(CartOrder, on_delete=models.CASCADE)
#     # Fields for full name, email, and mobile
#     full_name = models.CharField(max_length=1000)
#     email = models.CharField(max_length=1000)
#     mobile = models.CharField(max_length=1000)
    
#     # Method to return a string representation of the coupon code
#     def __str__(self):
#         return str(self.coupon.code)
    
#     class Meta:
#         ordering =['-id']

# Define a model for Delivery Couriers
class DeliveryCouriers(models.Model):

    FREE_DELIVERY = (
        ("Wschowa", "Wschowa"),
        ("Świdnica", "Świdnica"),
        ("Nowa Wieś", "Nowa Wieś"),
        ("Przyczyna Dolna", "Przyczyna Dolna"),
        ("Przyczyna Górna", "Przyczyna Górna"),
        ("Telewice", "Telewice"),
        ("Osowa Sień", "Osowa Sień"),
        ("Hetmanice", "Hetmanice"),
        ("Lgiń", "Lgiń"),
        ("Radomyśl", "Radomyśl"),
        ("Wjewo", "Wjewo"),
        ("Wieleń", "Wieleń"),
        ("Kaszczor", "Kaszczor"),
        ("Mochy", "Mochy"),
        ("Solec", "Solec"),
        ("Wolsztyn", "Wolsztyn"),
    )

    name = models.CharField(max_length=1000, null=True, blank=True)
    tracking_website = models.URLField(null=True, blank=True)
    url_parameter = models.CharField(null=True, blank=True, max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    free_delivery = models.CharField(choices=FREE_DELIVERY, null=True, blank=True)
    
    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Delivery Couriers"
    
    def __str__(self):
        return self.name