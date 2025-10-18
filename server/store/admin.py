from django.contrib import admin
from django import forms
from django.db.models import F

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse
import json

from django.utils.dateparse import parse_datetime

from import_export.admin import ImportExportModelAdmin
import requests

from store.models import *

@admin.action(description="Discount") #How to add 20% to the title/description?
def apply_discount(modeladmin, request, queryset):
    queryset.update(price=F('price') * 0.8) #20%

class GalleryInline(admin.TabularInline):
    model = Gallery

class SpecificationInline(admin.TabularInline):
    model = Specification

class SizeInline(admin.TabularInline):
    model = Size

class ColorInline(admin.TabularInline):
    model = Color

class CartOrderItemsInlineAdmin(admin.TabularInline):
    model = CartOrderItem

# class CouponUsersInlineAdmin(admin.TabularInline):
#     model = CouponUsers


class ProductAdminForm(forms.ModelForm):

    vendor = forms.ModelChoiceField(queryset=Vendor.objects.filter(user__is_staff=True))

    vendors = forms.ModelMultipleChoiceField(
        queryset=Vendor.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Product
        fields = '__all__'


class ProductAdmin(ImportExportModelAdmin):
# class ProductAdmin(admin.ModelAdmin):

    save_on_top = True

    # inlines = [ProductImagesAdmin, SpecificationAdmin, ColorAdmin, SizeAdmin]
    search_fields = ['title', 'price', 'slug', 'sku', 'ean',]
    list_filter = ['sku', 'status', 'in_stock', 'vendors']
    list_editable = ['image', 'title', 'ean', 'price', 'stock_qty', 'featured', 'status',  'shipping_amount', 'hot_deal', 'special_offer']
    list_display = ['sku', 'product_image', 'image', 'title', 'ean', 'price', 'featured', 'shipping_amount', 'in_stock' ,'stock_qty', 'status', 'featured', 'special_offer' ,'hot_deal']
    actions = [apply_discount, 'allegro_export', 'price_change']
    inlines = [GalleryInline, SpecificationInline, SizeInline, ColorInline]
    list_per_page = 100
    # prepopulated_fields = {"slug": ("title", )}
    form = ProductAdminForm

    offers = []

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # print("---- selected_vendors obj ----", obj)

        selected_vendors = obj.vendors.all().order_by('id')
        # print("---- selected_vendors main ----", selected_vendors)
        for vendor in selected_vendors:
            # print("---- selected_vendors ----", vendor.name)
            access_token = vendor.access_token

            offers = self.get_offers(access_token, vendor.name)
            # self.get_me(access_token, vendor.name) # To verify access token is valid
            # print("---- selected_offers ----", offers.text)

            for offer in offers.json()['offers']:
                # print('price_change MATCH ----------------', offer['external']['id'])
                if offer['external'] is not None:
                    if str(offer['external']['id']) == str(obj.sku):
                        # print('offer[id]----------------', offer['id'])

                        self.allegro_price_change(access_token, offer['id'], obj.price)
                        self.allegro_stock_change(access_token, offer['id'], obj.stock_qty)
                        offers = []
                else:
                    continue




    def allegro_export(self, request, queryset):

        print('allegro_export request.user ----------------', request.user)
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers"
        vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl')
        for vendor in vendors:
            print('allegro_export vendors ----------------', vendors)

        for vendor in vendors:
            access_token = vendor.access_token
            producer = self.responsible_producers(access_token)
            print('allegro_export producer ----------------', producer)
            for product in queryset:
                # print('allegro_export ----------------', product.ean)
                self.create_offer_from_product(product, url, access_token, producer)


    def responsible_producers(self, access_token):

        url = "https://api.allegro.pl.allegrosandbox.pl/sale/responsible-producers" 

        headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        print('create_offer_from_product response ----------------', response.text)
        return response.json()


    def create_offer_from_product(self, product, url, access_token, producer):

        print('create_offer_from_product producer ----------------', producer["responsibleProducers"][0]['id'])

        try:
            payload = json.dumps({
            "productSet": [
                {
                "product": {
                    "id": product.ean,
                    "idType": "GTIN"
                },
                "responsibleProducer": {
                    "type": "ID",
                    "id": producer["responsibleProducers"][0]['id']
                },
                },
            ],
            "sellingMode": {
                "price": {
                "amount": "220.85",
                "currency": "PLN"
                }
            },
            "stock": {
                "available": 10
            },
            'delivery': {
                'shippingRates': {
                    'name': 'Standard'
                }
            },
            })

            headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Content-Type': 'application/vnd.allegro.public.v1+json',
            'Accept-Language': 'pl-PL',
            'Authorization': f'Bearer {access_token}'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            print('create_offer_from_product response ----------------', response)
            return response
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
       

    def get_me(self, access_token, name):

        url = "https://api.allegro.pl.allegrosandbox.pl/me"

        headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        # print('get_me NAME ----------------', name)
        # print('get_me access_token ----------------', access_token)
        # print('get_me response ----------------', response.text)
        return response


    def get_offers(self, access_token, name):

        url = "https://api.allegro.pl.allegrosandbox.pl/sale/offers"

        headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        # print('get_offers NAME ----------------', name)
        # print('get_offers access_token ----------------', access_token)
        # print('get_offers response ----------------', response.text)
        return response
        

    def price_change(self, request, queryset):

        vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl')

        for product in queryset:  # Loop through selected products
            product_price = product.price 
            # print('product_price MATCH ----------------', product_price) 

            for vendor in vendors:
                access_token = vendor.access_token
                offers = self.get_offers(access_token, vendor.name)

                for offer in offers.json()['offers']:
                    # print('price_change MATCH ----------------', offer['external'])
                    if offer['external'] is not None:
                        if str(offer['external']['id']) == str(product.sku):
                            # print('offer[id]----------------', offer['id'])
                            self.allegro_price_change(access_token, offer['id'], product_price)


    def allegro_price_change(self, access_token, offer_id, new_price):

        try:
            url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{offer_id}"

            payload = {
                "sellingMode": {
                    "price": {
                        "amount": f"{new_price}",
                        "currency": "PLN"
                    }
                }
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.allegro.public.v1+json",
                "Content-Type": "application/vnd.allegro.public.v1+json"
            }

            response = requests.patch(url, headers=headers, data=json.dumps(payload))
            # print('allegro_price_change response ----------------', response.text)

        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        

    def allegro_stock_change(self, access_token, offer_id, quantity):

        try:
            url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{offer_id}"

            payload = {
                "stock": {
                    "available": quantity,
                    "unit": "UNIT"
                }
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.allegro.public.v1+json",
                "Content-Type": "application/vnd.allegro.public.v1+json"
            }

            response = requests.patch(url, headers=headers, data=json.dumps(payload))
            # print('allegro_price_change response ----------------', response.text)

        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

class TagAdmin(ImportExportModelAdmin):
    list_display = ['title', 'category', 'active']
    prepopulated_fields = {"slug": ("title", )}


class ProductReviewAdmin(ImportExportModelAdmin):
    list_editable = ['active']
    list_editable = ['active']
    list_display = ['user', 'product', 'review', 'reply' ,'rating', 'active']


class AddressAdmin(ImportExportModelAdmin):
    list_editable = ['status']
    list_display = ['user', 'full_name', 'status']

class DeliveryCouriersAdmin(ImportExportModelAdmin):
    list_editable = ['tracking_website']
    list_display = ['name', 'tracking_website']

class NotificationAdmin(ImportExportModelAdmin):
    list_editable = ['seen']
    list_display = ['order', 'seen', 'user', 'vendor', 'date']


class BrandAdmin(ImportExportModelAdmin):
    list_editable = [ 'active']
    list_display = ['title', 'brand_image', 'active']

class ProductFaqAdmin(ImportExportModelAdmin):
    list_editable = [ 'active', 'answer']
    list_display = ['user', 'question', 'answer' ,'active']


@admin.register(AllegroOrder)
class AllegroOrderAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'order_id', 'buyer_login', 'offer_name', 'quantity', 'price_amount', 'occurred_at', 'type']
    list_filter = ['vendor', 'type', 'occurred_at']
    search_fields = ['order_id', 'buyer_login', 'buyer_email', 'offer_name']

    change_list_template = "admin/store/allegroorder/change_list.html"

    def changelist_view(self, request, extra_context=None):
        self.fetch_and_store_allegro_orders()
        return super().changelist_view(request, extra_context=extra_context)

    def fetch_and_store_allegro_orders(self):
        vendors = Vendor.objects.filter(marketplace='allegro.pl')
        for vendor in vendors:
            try:
                url = "https://api.allegro.pl.allegrosandbox.pl/order/events"
                headers = {
                    'Accept': 'application/vnd.allegro.public.v1+json',
                    'Authorization': f'Bearer {vendor.access_token}'
                }
                response = requests.get(url, headers=headers)
                events = response.json().get('events', [])

                for event in events:
                    order = event.get('order', {})
                    for item in order.get('lineItems', []):
                        AllegroOrder.objects.update_or_create(
                            order_id=event['id'],
                            vendor=vendor,
                            defaults={
                                'buyer_login': order['buyer']['login'],
                                'buyer_email': order['buyer']['email'],
                                'offer_id': item['offer']['id'],
                                'offer_name': item['offer']['name'],
                                'quantity': item['quantity'],
                                'price_amount': item['price']['amount'],
                                'price_currency': item['price']['currency'],
                                'occurred_at': parse_datetime(event['occurredAt']),
                                'type': event['type'],
                            }
                        )
            except Exception as e:
                print(f"Error fetching orders for {vendor.name}: {e}")


class CartOrderAdmin(ImportExportModelAdmin):

    inlines = [CartOrderItemsInlineAdmin]
    search_fields = ['oid', 'full_name', 'email', 'mobile', 'delivery']
    list_editable = ['order_status', 'payment_status', 'delivery_status', 'shipping_label']
    list_filter = ['payment_status', 'order_status', 'delivery_status', 'delivery']
    list_display = ['oid', 'payment_status', 'order_status', 'delivery', 'shipping_label', 'delivery_status', 'sub_total', 'shipping_amount', 'total', 'date']
    actions = ['generate_pdf_labels']


    def generate_pdf_labels(self, request, queryset):
        """Generate a PDF with shipping labels & product list."""
        
        # Create a BytesIO buffer to hold the PDF content
        buffer = BytesIO()
        
        # Create the PDF in the buffer
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Set starting position for the content
        y_position = height - 50

        # # Draw the border
        # c.rect(10, y_position - 10, width - 40, 20, stroke=1, fill=0)

        # Determine the top and bottom positions for the box
        top_y = height - 20  # Start near the top of the page
        bottom_y = y_position - 25  # A little below the last row

        # Draw a single large rectangle covering all orders
        c.rect(10, bottom_y, width - 40, top_y - bottom_y, stroke=1, fill=0)


        for order in queryset:
            # Add the order details (order summary)
            c.setFont("Helvetica-Bold", 12)
            c.setFont("Helvetica", 10)

            # Draw the border
            # c.rect(10, y_position - 5, width - 40, 20, stroke=1, fill=0)

            # Add product list (CartOrderItems)
            items = order.orderitem.all()  # Assuming you have a related name for CartOrderItem
            for item in items:
                # Title on the left and quantity on the right
                c.drawString(20, y_position, f"{item.product.title}")  # Title on the left
                c.drawString(width - 50, y_position, f"{item.qty}")  # Quantity on the right
                # Draw underline for the current row
                # c.line(20, y_position - 5, width - 50, y_position - 5)

                y_position -= 20

            # y_position -= 10  # Add some space between orders
        
            # Add a page if the content exceeds the page height
            if y_position < 100:
                c.showPage()
                y_position = height - 50  # Reset to the top of the next page

        # Finalize and save the PDF content into the buffer
        c.save()

        # Get the buffer value and prepare the response
        buffer.seek(0)  # Rewind the buffer to the beginning
        response = HttpResponse(buffer, content_type='application/pdf')

        # Optionally, set a filename for the downloaded PDF
        response['Content-Disposition'] = 'attachment; filename="shipping_labels_and_products.pdf"'

        # Close the buffer
        buffer.close()

        return response

    generate_pdf_labels.short_description = "Generuj liste zamówień"

class CartOrderItemsAdmin(ImportExportModelAdmin):
    list_filter = ['order__oid', 'date']
    list_editable = ['date']
    list_display = ['order_oid', 'product__sku', 'product_image', 'product' ,'qty', 'price', 'service_fee', 'tax_fee', 'date']


class CartAdmin(ImportExportModelAdmin):
    list_display = ['product', 'cart_id', 'qty', 'price', 'sub_total' , 'shipping_amount', 'service_fee', 'tax_fee', 'total', 'country', 'size', 'color', 'date']

class ReturnItemAdmin(ImportExportModelAdmin):
    search_fields = ['order__oid', 'order__full_name', 'order__email', 'order__mobile', 'return_status', 'return_decision', 'product__title', 'product__sku']
    list_editable = ['return_status', 'return_decision']
    list_filter = ['return_status', 'return_decision']
    list_display = ['order', 'product__sku', 'product_image', 'product', 'qty', 'return_reason', 'return_status', 'return_decision', 'return_delivery_courier']

    def save_model(self, request, obj, form, change):
        """
        Update the return data of the related CartOrderItem whenever ReturnItem is saved.
        """
        super().save_model(request, obj, form, change)
        
        if obj.order_item:
            obj.order_item.return_decision = obj.return_decision
            obj.order_item.return_delivery_courier = obj.return_delivery_courier
            obj.order_item.return_tracking_id = obj.return_tracking_id
            obj.order_item.save() 

class CouponAdmin(ImportExportModelAdmin):
    # inlines = [CouponUsersInlineAdmin]
    list_editable = ['code', 'active', ]
    list_display = ['vendor' ,'code', 'discount', 'active', 'date']


admin.site.register(Product, ProductAdmin)
admin.site.register(Review, ProductReviewAdmin)
admin.site.register(Category)
admin.site.register(Gallery)
admin.site.register(Tag, TagAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartOrderItem, CartOrderItemsAdmin)
admin.site.register(ReturnItem, ReturnItemAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(ProductFaq, ProductFaqAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Wishlist)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(DeliveryCouriers, DeliveryCouriersAdmin)
