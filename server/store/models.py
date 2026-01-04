import datetime
from decimal import ROUND_HALF_UP, Decimal
import os
from django.db import models
from django.utils.html import mark_safe
from django.utils.text import slugify
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.db.models import F

from store.utils.invoice import invoice_upload_path
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
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ["title"]

    def thumbnail(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.image.url))

    def __str__(self):
        # return f'{self.title} - {self.allegro_cat_id}' ## allegro
        return self.title ## kecja
    
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


# models.py

class SeoTitleBatch(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="PENDING")
    total_products = models.PositiveIntegerField(default=0)
    processed_products = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"SEO Batch {self.id}"


class SeoTitleLog(models.Model):
    batch = models.ForeignKey(SeoTitleBatch, on_delete=models.CASCADE, related_name="logs")
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    new_title = models.CharField(max_length=255, null=True, blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Log for product {self.product_id} in batch {self.batch_id}"


class AllegroProductBatch(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="PENDING")

    total_products = models.PositiveIntegerField(default=0)
    processed_products = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"UpdateBatch {self.id} ({self.status})"
    

class AllegroProductUpdateLog(models.Model):
    batch = models.ForeignKey(AllegroProductBatch, on_delete=models.CASCADE, related_name="logs")
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    updates = models.JSONField(default=list)   # np. ["price_brutto", "stock_qty"]
    success = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for product {self.product_id} in batch {self.batch_id}"




class Product(models.Model):

    MARKETPLACE_CHOICES = (
        ('shop', 'Web Shop'),
        ('allegro_1', 'Allegro Account 1'),
        ('allegro_2', 'Allegro Account 2'),
    )

    STATUS = (
        ("draft", "Product is draft"),
        ("disabled", "Product is disabled"),
        ("rejected", "Product is rejected"),
        ("in_review", "Product is in review"),
        ("published", "Product is published"),
    )

    # ALLEGRO_STATUS = (
    #     ("ACTIVE", "Product aktywny"),
    #     ("INACTIVE", "Produkt nieaktywny"), 
    #     ("ACTIVATING", "Aukcja planowana lub w czasie wystawiania"),
    #     ("ENDED", "Aukcja zakończona"),
    # )

    ALLEGRO_STATUS = (
        ("ACTIVE", "✅"),
        ("INACTIVE", "⛔"),
        ("ACTIVATING", "⏳"),
        ("ENDED", "🏁"),
    )


    PRODUCT_TYPE = (
        ("regular", "Regular"),
        ("auction", "Auction"),
        ("offer", "Offer")
    )

    # allegro_id = models.CharField(max_length=100, null=True, blank=True)
    allegro_ids = models.JSONField(default=list, blank=True)
    title = models.CharField(max_length=255, verbose_name='Nazwa')
    ean = models.CharField(max_length=100, null=True, blank=True)
    image = models.FileField(upload_to="products", max_length=1000, blank=True, null=True, default="default.jpg")
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    img_links = models.JSONField(blank=True, null=True)
    description = models.TextField(null=True, blank=True, verbose_name="Opis")
    text_description = models.TextField(max_length=5000,null=True, blank=True, verbose_name="Opis textowy")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="category")
    sub_cat = models.JSONField(null=True, blank=True)
    tags = models.CharField(max_length=1000, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, verbose_name='Cena netto')
    price_brutto = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, verbose_name='Cena brutto')
    hurt_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, verbose_name='Cena hurtowa brutto')
    prowizja_allegro = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, verbose_name='Prowizja allegro')
    zysk_pln = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Zysk w PLN")
    zysk_procent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Zysk w %")
    zysk_after_payments = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Zysk", help_text='Zysk -dostawa i -3%')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("23.00"))
    reach_out = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("3.00"))
    old_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, verbose_name="Cena przed obniżką")
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Koszt dostawy sklep")
    allegro_delivery_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Koszt dostawy allegro")
    stock_qty = models.PositiveIntegerField(default=0, verbose_name="Ilość")
    in_stock = models.BooleanField(default=True, verbose_name="Sklep")

    # Product status and type
    status = models.CharField(choices=STATUS, max_length=50, default="published", null=True, blank=True)
    type = models.CharField(choices=PRODUCT_TYPE, max_length=50, default="regular")

    allegro_status = models.CharField(choices=ALLEGRO_STATUS, max_length=50, default="published", verbose_name="allegro status", null=True, blank=True)
    allegro_in_stock = models.BooleanField(default=False, verbose_name="allegro")

    updates = models.BooleanField(default=False, verbose_name="aktualizacje")
    
    # Product flags (featured, hot deal, special offer, digital)
    featured = models.BooleanField(default=False, verbose_name='Nowości')
    hot_deal = models.BooleanField(default=False, verbose_name='Rabat')
    special_offer = models.BooleanField(default=False, verbose_name='Popularne')
    digital = models.BooleanField(default=False)
    
    # Product statistics (views, orders, saved, rating)
    views = models.PositiveIntegerField(default=0, null=True, blank=True)
    orders = models.PositiveIntegerField(default=0, null=True, blank=True)
    saved = models.PositiveIntegerField(default=0, null=True, blank=True)
    rating = models.IntegerField(default=0, null=True, blank=True)

    # Vendor associated with the product
    # vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name="vendor")
    vendors = models.ManyToManyField(Vendor, blank=True, verbose_name="Sprzedawca")
    
    # Unique short UUIDs for SKU and product
    sku = models.CharField(max_length=150, null=True, blank=True)
    pid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefghijklmnopqrstuvxyz")
    
    # Slug for SEO-friendly URLs
    slug = models.SlugField(max_length=255, null=True, blank=True,)
    date = models.DateTimeField(default=timezone.now)

    # Parameters
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True, help_text="Waga w kg")
    height = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True, help_text="Wysokość w cm")
    width = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True, help_text="Szerokość w cm")
    depth = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True, help_text="Głębokość w cm")

    class Meta:
        ordering = ['-id']
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"



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
        # 🔒 Normalize all numeric fields to Decimal
        def to_dec(x, default="0"):
            return x if isinstance(x, Decimal) else Decimal(str(x if x is not None else default))

        self.hurt_price             = to_dec(getattr(self, "hurt_price", None), "0")
        self.price                  = to_dec(getattr(self, "price", None), "0")
        self.price_brutto           = to_dec(getattr(self, "price_brutto", None), "0")
        self.zysk_pln               = to_dec(getattr(self, "zysk_pln", None), "0")
        self.zysk_after_payments    = to_dec(getattr(self, "zysk_after_payments", None), "0")
        self.zysk_procent           = to_dec(getattr(self, "zysk_procent", None), "0")
        self.tax_rate               = to_dec(getattr(self, "tax_rate", None), "0")

        print("zysk_after_payments ------------", self.zysk_after_payments)  
        _zysk_after_payments = self.zysk_after_payments 
        

        def calculate_delivery_cost(cena_brutto: Decimal, przesylki: int = 1) -> Decimal:
            """
            Oblicza koszt dostawy na podstawie ceny brutto i liczby przesyłek.
            """
            if cena_brutto < Decimal("30"):
                return Decimal("0.00")  # poniżej 30 zł np. brak obsługi
            elif cena_brutto <= Decimal("44.99"):
                return Decimal("1.59") * przesylki
            elif cena_brutto <= Decimal("64.99"):
                return Decimal("3.09") * przesylki
            elif cena_brutto <= Decimal("99.99"):
                return Decimal("4.99") * przesylki
            elif cena_brutto <= Decimal("149.99"):
                return Decimal("7.59") * przesylki
            else:
                # od 150 zł: pierwsza przesyłka 9.99, kolejne 7.59
                if przesylki == 1:
                    return Decimal("9.99")
                else:
                    return Decimal("9.99") + Decimal("7.59") * (przesylki - 1)

        # 🔑 Generate slug
        uuid_key = shortuuid.uuid()
        uniqueid = uuid_key[:4]
        self.slug = slugify(self.title) + "-" + str(uniqueid.lower())

        vat_multiplier = Decimal("1") + self.tax_rate / Decimal("100")

        # 📦 Get old version from DB (if exists)
        old = None
        if self.pk:
            try:
                old = Product.objects.get(pk=self.pk)
            except Product.DoesNotExist:
                pass

        # --- Nowa logika: zysk po odjęciu 3% i kosztów dostawy ---
        if self.price_brutto and self.hurt_price:
            # Odejmij 3% od ceny brutto
            cena_po_prowizji = (self.price_brutto * Decimal("0.97")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Koszt dostawy (zakładamy 1 przesyłkę)
            delivery_cost = calculate_delivery_cost(cena_po_prowizji, przesylki=1)

            # Zysk po odjęciu prowizji i dostawy
            self.zysk_after_payments = (cena_po_prowizji - self.hurt_price - delivery_cost - self.prowizja_allegro).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 4️⃣ If price (netto) changed after Kecja price updates
        elif old and self.price != old.price and self.hurt_price is not None:
            cena_brutto = (self.price * vat_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if cena_brutto > self.price_brutto:
                self.price_brutto = (cena_brutto - old.price_brutto + self.price_brutto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                self.price_brutto = (self.price_brutto - (cena_brutto - old.price_brutto)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            # Nowa logika zysku po prowizji i dostawie
            cena_po_prowizji = (self.price_brutto * Decimal("0.97")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            delivery_cost = calculate_delivery_cost(cena_po_prowizji, przesylki=1)
            delivery_cost = Decimal(str(delivery_cost))
            prowizja = Decimal(str(self.prowizja_allegro))
            self.zysk_after_payments = (cena_po_prowizji - self.hurt_price - delivery_cost - prowizja).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # print("Zysk PLN TEST old ------------", old)
        # print("Zysk PLN TEST hurt_price ------------", self.hurt_price)
        # print("Zysk PLN TEST old.zysk_after_payments ------------", old.zysk_after_payments)
        # print("Zysk PLN TEST zysk_after_payments ------------", self.zysk_after_payments)

        # # 1️⃣ If zysk changed
        # if old and _zysk_after_payments != old.zysk_after_payments and self.hurt_price is not None:
        #     print("Zysk PLN changed------------")
        #     cena_do_prowizji = (self.hurt_price + _zysk_after_payments ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     print("Zysk PLN cena_do_prowizji ------------", cena_do_prowizji)
        #     cena_po_prowizji = (cena_do_prowizji * Decimal("1.03")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     print("Zysk PLN cena_po_prowizji ------------", cena_po_prowizji)
        #     # Koszt dostawy (zakładamy 1 przesyłkę)
        #     delivery_cost = calculate_delivery_cost(cena_po_prowizji, przesylki=1)
        #     print("Zysk PLN delivery_cost ------------", delivery_cost)
        #     self.price_brutto = (cena_po_prowizji + delivery_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     print("Zysk PLN price_brutto ------------", self.price_brutto)
        #     self.price = (self.price_brutto / vat_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     self.zysk_after_payments = _zysk_after_payments
        #     self.zysk_procent = (self.zysk_after_payments / self.hurt_price * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if self.hurt_price > 0 else Decimal("0.00")
            

        # 2️⃣ If zysk_procent changed
        # if old and self.zysk_procent != old.zysk_procent and self.hurt_price is not None:
        #     cena_brutto = (self.hurt_price * (Decimal("1") + self.zysk_procent / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     self.price = (cena_brutto / vat_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     self.price_brutto = cena_brutto
        #     self.zysk_after_payments = (cena_brutto - self.hurt_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # # 3️⃣ If price_brutto changed
        # elif old and self.price_brutto != old.price_brutto and self.hurt_price is not None:
        #     cena_brutto = self.price_brutto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     self.price = (cena_brutto / vat_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     self.zysk_after_payments = (cena_brutto - self.hurt_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     self.zysk_procent = (self.zysk_pln / self.hurt_price * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if self.hurt_price > 0 else Decimal("0.00")

        # # 4️⃣ If price (netto) changed after Kecja price updates
        # elif old and self.price != old.price and self.hurt_price is not None:
        #     cena_brutto = (self.price * vat_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     if cena_brutto > self.price_brutto:
        #         self.price_brutto = (cena_brutto - old.price_brutto + self.price_brutto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     else:
        #         self.price_brutto = (self.price_brutto - old.price_brutto + cena_brutto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     self.zysk_after_payments = (cena_brutto - self.hurt_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        #     self.zysk_procent = (self.zysk_pln / self.hurt_price * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if self.hurt_price > 0 else Decimal("0.00")

        super().save(*args, **kwargs)

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
        verbose_name = "Tag"
        verbose_name_plural = "Tagi"
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
    
    class Meta:
        verbose_name = "Koszyk"
        verbose_name_plural = "Koszyki"


def label_upload_path(instance, filename):
    today = datetime.date.today().strftime("%Y-%m-%d")
    return f"allegro_labels/{today}/{filename}"



class AllegroBatch(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    zip_file = models.FileField("Etykieta przewozowa", upload_to=label_upload_path, null=True, blank=True)
    status = models.CharField(max_length=20, default="PENDING")
    processed_orders = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)


    def __str__(self):
        return f"Batch {self.id} ({self.status})"
    

class AllegroLabel(models.Model):
    # batch = models.ForeignKey(AllegroBatch, on_delete=models.CASCADE, related_name="labels", verbose_name="Partia Allegro")
    order = models.ForeignKey(
        "AllegroOrder", 
        on_delete=models.CASCADE, 
        related_name="labels", 
        verbose_name="Zamówienie Allegro",
        null=True, 
        blank=True,
    )
    zip_file = models.FileField("Etykieta przewozowa", upload_to=label_upload_path, null=True, blank=True)

    def __str__(self):
        return f"Label for Order {self.order.order_id} in Batch {self.batch.id}"

    

class AllegroOrder(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, verbose_name="Sprzedawca")
    event_id = models.CharField("ID zdarzenia", max_length=300, unique=True, null=True, blank=True)
    order_id = models.CharField("ID zamówienia", max_length=300, null=True, blank=True)
    commandId = models.CharField("ID komendy", max_length=300, null=True, blank=True)
    shipmentId = models.CharField("ID przesyłki", max_length=300, null=True, blank=True)
    delivery_method_id = models.CharField("ID metody dostawy", max_length=300, null=True, blank=True)
    delivery_method_name = models.CharField("Nazwa metody dostawy", max_length=300, null=True, blank=True)
    pickup_point_id = models.CharField("ID punktu odbioru", max_length=300, null=True, blank=True)
    pickup_point_name = models.CharField("Nazwa punktu odbioru", max_length=300, null=True, blank=True)
    label_file = models.FileField("Etykieta przewozowa", upload_to=label_upload_path, null=True, blank=True)
    # label_file = models.ManyToManyField(AllegroLabel, blank=True, null=True, verbose_name="Etykiety przewozowe")
    buyer_login = models.CharField("Login kupującego", max_length=100)
    buyer_email = models.EmailField("E-mail kupującego")
    buyer_name = models.CharField("Imię i nazwisko", max_length=100, null=True, blank=True)
    buyer_company_name = models.CharField("Nazwa firmy", max_length=100, null=True, blank=True)
    buyer_street = models.CharField("Ulica", max_length=100, null=True, blank=True)
    buyer_zipcode = models.CharField("Kod pocztowy", max_length=100, null=True, blank=True)
    buyer_city = models.CharField("Miasto", max_length=100, null=True, blank=True)
    buyer_nip = models.CharField("NIP", max_length=100, null=True, blank=True)
    is_smart = models.BooleanField("Dostawa SMART", default=False)
    delivery_cost = models.DecimalField("Koszt dostawy", max_digits=10, decimal_places=2, default=0.00)
    delivery_address = models.JSONField("Adres dostawy", null=True, blank=True)
    occurred_at = models.DateTimeField("Data zakupu")
    type = models.CharField("Typ zdarzenia", max_length=50)
    invoice_generated = models.BooleanField("Faktura wygenerowana", default=False)
    stock_updated = models.BooleanField("Stan magazynowy zaktualizowany", default=False)
    message = models.ForeignKey("Message", on_delete=models.CASCADE, verbose_name="Auto Widomość", null=True, blank=True)
    message_sent = models.BooleanField("Wiadomość", default=False)
    error = models.CharField("Błąd", max_length=1000, null=True, blank=True)

    class Meta:
        verbose_name = "Zamówienie Allegro"
        verbose_name_plural = "Zamówienia Allegro"

    def __str__(self):
        return self.order_id

    # def __str__(self):
    #     # This is what the autocomplete dropdown shows
    #     return f"{self.order_id or '—'} · {self.buyer_login or ''} · {self.vendor.name if self.vendor_id else ''}"


class AllegroOrderItem(models.Model):
    order = models.ForeignKey(AllegroOrder, on_delete=models.CASCADE, related_name="items", verbose_name="Zamówienie Allegro")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produkt")
    offer_id = models.CharField("ID oferty", max_length=100)
    offer_name = models.CharField("Nazwa oferty", max_length=255)
    quantity = models.PositiveIntegerField("Ilość", default=1)
    price_amount = models.DecimalField("Cena", max_digits=10, decimal_places=2)
    price_currency = models.CharField("Waluta", max_length=3, default="PLN")
    tax_rate = models.DecimalField("Stawka VAT", max_digits=5, decimal_places=2, default=23.00)

    class Meta:
        verbose_name = "Pozycja zamówienia Allegro"
        verbose_name_plural = "Pozycje zamówienia Allegro"

    def __str__(self):
        return f"{self.offer_name} x {self.quantity}"
    

class Message(models.Model):
    title = models.CharField("Tytuł", max_length=155, null=True, blank=True)
    text = models.CharField("Tekst wiadomości", max_length=2000, null=True, blank=True)

    class Meta:
        verbose_name = "Auto wiadomość"
        verbose_name_plural = "Auto wiadomości"

    def __str__(self):
        return f"{self.id}"


class Invoice(models.Model):
    invoice_number = models.CharField("Numer faktury", max_length=100, unique=True, editable=True)
    created_at = models.DateTimeField("Data wygenerowania", auto_now_add=True)
    # generated_at = models.DateTimeField("Data wygenerowania", null=True, blank=True)
    shop_order = models.ForeignKey("CartOrder", on_delete=models.CASCADE, null=True, blank=True, verbose_name="Zamówienie sklepu")
    allegro_order = models.ForeignKey(AllegroOrder, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Zamówienie Allegro")
    order = models.CharField("Numer zamówienia", max_length=255, null=True, blank=True)
    buyer_name = models.CharField("Nabywca", max_length=100)
    buyer_company_name = models.CharField("Firma nabywcy", max_length=100, null=True, blank=True)
    buyer_email = models.EmailField("E-mail nabywcy", null=True, blank=True)
    buyer_street = models.CharField("Ulica", max_length=100, null=True, blank=True)
    buyer_zipcode = models.CharField("Kod pocztowy", max_length=100, null=True, blank=True)
    buyer_city = models.CharField("Miasto", max_length=100, null=True, blank=True)
    buyer_nip = models.CharField("NIP", max_length=100, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, verbose_name="Sprzedawca")
    is_generated = models.BooleanField("Wygenerowana", default=False)
    sent_to_buyer = models.BooleanField("Wysłana do kupującego", default=False)
    corrected = models.BooleanField("Skorygowana", default=False)

    class Meta:
        verbose_name = "Faktura"
        verbose_name_plural = "Faktury"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            if not self.created_at:
                self.created_at = timezone.now()

            year = self.created_at.year
            month = self.created_at.month

            count = Invoice.objects.filter(
                created_at__year=year,
                created_at__month=month
            ).count()

            current_number = count + 1
            formatted_number = str(current_number).zfill(5)
            date_part = self.created_at.strftime('%m/%Y')

            self.invoice_number = f"FV-{formatted_number}/{date_part}"

        super().save(*args, **kwargs)


class InvoiceCorrection(models.Model):
    invoice_number = models.CharField("Numer korekty", max_length=100, unique=True, editable=False)
    main_invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="corrections", null=True, blank=True, verbose_name="Faktura główna")
    created_at = models.DateTimeField("Data wygenerowania", auto_now_add=True)
    # generated_at = models.DateTimeField("Data wygenerowania", null=True, blank=True)
    shop_order = models.ForeignKey("CartOrder", on_delete=models.CASCADE, null=True, blank=True, verbose_name="Zamówienie sklepu")
    allegro_order = models.ForeignKey(AllegroOrder, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Zamówienie Allegro")
    order = models.CharField("Numer zamówienia", max_length=255, null=True, blank=True)
    products = models.JSONField("Produkty (JSON)", null=True, blank=True)
    buyer_name = models.CharField("Nabywca", max_length=100)
    buyer_company_name = models.CharField("Firma nabywcy", max_length=100, null=True, blank=True)
    buyer_email = models.EmailField("E-mail nabywcy", null=True, blank=True)
    buyer_street = models.CharField("Ulica", max_length=100, null=True, blank=True)
    buyer_zipcode = models.CharField("Kod pocztowy", max_length=100, null=True, blank=True)
    buyer_city = models.CharField("Miasto", max_length=100, null=True, blank=True)
    buyer_nip = models.CharField("NIP", max_length=100, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, verbose_name="Sprzedawca")
    is_generated = models.BooleanField("Wygenerowana", default=False)
    sent_to_buyer = models.BooleanField("Wysłana do kupującego", default=False)

    class Meta:
        verbose_name = "Korekta faktury"
        verbose_name_plural = "Korekty faktur"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            if not self.created_at:
                self.created_at = timezone.now()

            year = self.created_at.year
            month = self.created_at.month

            count = InvoiceCorrection.objects.filter(
                created_at__year=year,
                created_at__month=month
            ).count()

            current_number = count + 1
            formatted_number = str(current_number).zfill(5)
            date_part = self.created_at.strftime('%d/%m/%Y')

            self.invoice_number = f"FV-{formatted_number}/KOR/{date_part}"

        super().save(*args, **kwargs)


class InvoiceFile(models.Model):
    order = models.ForeignKey(
        "CartOrder",
        on_delete=models.CASCADE,
        related_name="invoices"
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    invoice_correction = models.ForeignKey(
        InvoiceCorrection,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to=invoice_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)

    # @property
    # def invoice_number(self):
    #     return getattr(self.order, "invoice_number", None)

    @property
    def invoice_number(self):
        if self.invoice:
            return self.invoice.invoice_number
        return self.order.oid

    def __str__(self):
        if self.invoice:
            return f"Invoice {self.invoice.invoice_number} for order {self.order.oid}"
        else:
            return f"Invoice {self.invoice_correction.invoice_number} for order {self.order.oid}"


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
    # product = models.ForeignKey('CartOrderItem', related_name="items", on_delete=models.CASCADE, null=True)
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
    stock_updated = models.BooleanField(default=False)

    # Invoice
    invoice_generated = models.BooleanField(default=False, null=True, blank=True)
    
    # Discounts
    initial_total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="The original total before discounts")
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Amount saved by customer")
    
    # Personal Informations
    full_name = models.CharField(max_length=1000)
    email = models.CharField(max_length=1000)
    mobile = models.CharField(max_length=1000)
    buyer_nip = models.CharField("NIP", max_length=100, null=True, blank=True)
    
     # Shipping Address
    street = models.CharField(max_length=1000, null=True, blank=True)
    number = models.CharField(max_length=1000, null=True, blank=True)
    post_code = models.CharField(max_length=1000, null=True, blank=True)
    city = models.CharField(max_length=1000, null=True, blank=True)

    # coupons = models.ManyToManyField('store.Coupon', blank=True)
    
    stripe_session_id = models.CharField(max_length=200,null=True, blank=True)
    # oid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")
    oid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payu_order_id = models.CharField(max_length=500, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ["-date"]
        verbose_name = "Zamówienie"
        verbose_name_plural = "Zamówienia"

    def __str__(self):
        return str(self.oid)

    def get_order_items(self):
        return CartOrderItem.objects.filter(order=self)

    # def get_order_items(self):
    #     return CartOrder.objects.filter(order=self)
    #     # return self.items.all()
    
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
        ("Koszty zwrócone Payu", 'Koszty zwrócone Payu'),
        ("Koszty zwrócone Email", 'Koszty zwrócone Email'),
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
    refund_processed = models.BooleanField(default=False)

    def order_oid(self):
        return self.order.oid
    
    def product_sku(self):
        return self.product.sku
    
    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.product.image.url))

    class Meta:
            verbose_name = "Zwrot"
            verbose_name_plural = "Zwroty"

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

    class Meta:
        verbose_name = "Zamówiony przedmiot"
        verbose_name_plural = "Zamówione przedmioty"

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
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Szerokość (cm)")
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Wysokość (cm)")
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Długość (cm)")
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Waga (kg)")
    
    class Meta:
        ordering = ["name"]
        verbose_name = "Przewoźnik dostaw"
        verbose_name_plural = "Przewoźnicy dostaw"
    
    def __str__(self):
        return self.name
    

class ClientAccessLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    device_type = models.CharField(max_length=20, blank=True, null=True)
    operating_system = models.CharField(max_length=20, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    geo_location = models.JSONField(blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    referer = models.URLField(blank=True, null=True)
    cookies = models.TextField(blank=True, null=True)
    accessed_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = "Informacje o użytkownikach"
        ordering = ['-accessed_at']

    def __str__(self):
        return f"{self.ip_address} ({self.device_type}) at {self.accessed_at} in {self.geo_location}"
