from django.contrib import admin
from django.shortcuts import redirect, render
from django import forms
from django.db.models import F
from django.utils.timezone import now
from django.utils.html import format_html, format_html_join
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
from django.urls import path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO, StringIO
import requests, json, csv
import zipfile
import os
from dotenv import load_dotenv

from import_export.admin import ImportExportModelAdmin

from .utils.payu import payu_authenticate, to_grosze
from store.allegro_views.views import allegro_request
from store.utils.invoice import *
from store.utils.decimal import *
from store.models import *
from store.tasks import *

# Load variables from .env into environment
load_dotenv()

# Access them like normal environment variables
ALLEGRO_API_URL = os.getenv("ALLEGRO_API_URL")
PAYU_API_URL = os.getenv("PAYU_API_URL")
_marketplace = os.getenv("marketplace")


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

class ClientAccessLogInline(admin.TabularInline):
    model = ClientAccessLog
    readonly_fields = ('ip_address', 'user_agent', 'device_type', 'operating_system', 'geo_location', 'language', 'referer', 'cookies', 'accessed_at')
    can_delete = False
    extra = 0

class ClientAccessLogAdmin(ImportExportModelAdmin):
    list_display = ('ip_address', 'device_type', 'operating_system', 'geo_location', 'accessed_at', 'referer')
    list_filter = ('device_type', 'operating_system', 'accessed_at')
    search_fields = ('ip_address', 'user_agent', 'geo_location', 'referer', 'cookies')
    readonly_fields = ('ip_address', 'user_agent', 'device_type', 'operating_system', 'geo_location', 'language', 'referer', 'cookies', 'accessed_at')


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
    search_fields = ['title', 'price', 'slug', 'sku', 'ean']
    list_filter = ['sku', 'vendors', 'stock_qty']
    list_editable = ['title','ean', 'price', 'tax_rate', 'stock_qty', 'hot_deal', 'in_stock']
    list_display = ['sku', 'product_image', 'allegro_in_stock', 'allegro_status', 'in_stock', 'title', 'title_warning', 'stock_qty', 'ean', 'price', 'tax_rate', 'price_brutto', 'hurt_price', 'price_zysk', 'price_zysk_percent', 'hot_deal']
    # exclude = ('vendors',) 
    actions = [apply_discount, 'allegro_export', 'allegro_update', 'sync_allegro_offers']
    inlines = [GalleryInline, SpecificationInline, SizeInline, ColorInline]
    list_per_page = 100
    # prepopulated_fields = {"slug": ("title", )}
    form = ProductAdminForm

    change_list_template = "admin/store/product/change_list.html"

    class Media:
        css = {
            "all": ("admin/css/custom_styles/my.css",)
        }

    offers = []

    def title_warning(self, obj):
        if len(obj.title or "") > 75:
            return format_html('<span style="color:red;">⚠️ {} znaków</span>', len(obj.title))
        return ""
    title_warning.short_description = "Ostrzeżenie"

    title_warning.short_description = "Tytuł"

    def product_image(self, obj):  # assuming Gallery model has 'image' field
        if obj.thumbnail:
            return format_html('<img src="{}" width="60" height="60" style="object-fit:cover; border-radius:6px;" />', obj.thumbnail.url)
        return format_html('<span style="color: #999;">No image</span>')


    product_image.short_description = "Zdjęcie"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "vendor":
            # Only show the vendors for current user and marketplace
            kwargs["queryset"] = Vendor.objects.filter(user=request.user, marketplace=_marketplace)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    

    def fetch_all_offers(self, vendor_name, headers):

        all_offers = []
        offset = 0
        limit = 1000

        url = f"https://{ALLEGRO_API_URL}/sale/offers?limit={limit}&offset={offset}"

        while True:
            offers_url = f"https://{ALLEGRO_API_URL}/sale/offers?limit={limit}&offset={offset}"
            response = allegro_request('GET', url, vendor_name, headers=headers)
            data = response.json()
            offers = data.get("offers", [])
            all_offers.extend(offers)

            if len(offers) < limit:
                break  # nie ma już więcej wyników
            offset += limit

        return all_offers
    

    def sync_allegro_offers(self, request, queryset):

        vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl')

        for vendor in vendors:
            # print('check vendor ----------------', vendor)
            access_token = vendor.access_token

            headers = {
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Authorization': f'Bearer {access_token}'
            }
            try:
                products = Product.objects.all()
                offers = self.fetch_all_offers(vendor.name, headers)
                product_map = {obj.sku: obj for obj in products}

                for offer in offers:
                    external = offer.get("external")
                    if not external:
                        continue

                    sku = external.get("id")
                    product = product_map.get(sku)
                    if not product:
                        continue

                    status = offer.get("publication", {}).get("status")
                    if status == "ACTIVE":
                        product.allegro_in_stock = True
                        price_brutto = Decimal(
                            offer.get("sellingMode", {}).get("price", {}).get("amount", "0")
                        )

                        # netto = brutto / 1.23
                        price_netto = (price_brutto / Decimal("1.23")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                        product.price = price_netto
                    else:
                        product.allegro_in_stock = False
                    product.allegro_status = status

                    product.save(update_fields=["allegro_in_stock", "allegro_status", "price"])

                self.message_user(request, f"Twoje oferty zostały zaktualizowane", level="success")

                if "errors" in offers:
                    self.message_user(request, f"⚠️ {offers['errors'][0]['message']}", level="error")
            except Exception as e:
                self.message_user(request, f"❌ Błąd zapytania: {str(e)}", level="error")

    sync_allegro_offers.short_description = "🔄 Synchronizuj z Allegro"


#    def save_model(self, request, obj, form, change):

        # - 20% round to second number after coma (Exp: 12.99PLN)  
        # if obj.price:
        #     obj.price = (obj.price * Decimal('0.8')).quantize(Decimal('0.01'))
#        print('*********************save_model*******************')

#        pass

        # super().save_model(request, obj, form, change)

        # # vendors = Vendor.objects.filter(user=request.user, marketplace=_marketplace)
        # vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl')
        # obj.vendors.set(vendors)

        # # print("---- selected_vendors obj ----", obj)

        # selected_vendors = obj.vendors.all().order_by('id')
        # # print("---- selected_vendors main ----", selected_vendors)
        # for vendor in selected_vendors:
        #     # print("---- selected_vendors ----", vendor.name)
        #     try:
        #         access_token = vendor.access_token

        #         offers = self.get_offers(access_token, vendor.name)
        #         self.get_me(access_token, vendor.name) # To verify access token is valid
        #         # print("---- selected_offers ----", offers.text)

        #         for offer in offers.json()['offers']:
        #             # print('price_change MATCH ----------------', offer['external']['id'])
        #             if offer['external'] is not None:
        #                 if str(offer['external']['id']) == str(obj.sku):
        #                     # print('offer[id]----------------', offer['id'])

        #                     self.allegro_price_change(request, access_token, vendor.name, offer['id'], obj.price)
        #                     self.allegro_stock_change(request, access_token, vendor.name, offer['id'], obj.stock_qty)
        #                     self.allegro_title_change(request, access_token, vendor.name, offer['id'], obj.title)
        #                     offers = []
        #             else:
        #                 continue
        #     except:
        #         continue


    
    # def get
    


    def allegro_update(self, request, queryset):
        # print('allegro_export request.user ----------------', request.user)
        vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl')

        for vendor in vendors:
            # print('check vendor ----------------', vendor)
            access_token = vendor.access_token

            headers = {
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json',
                'Accept-Language': 'pl-PL',
                'Authorization': f'Bearer {access_token}'
            }
        
            for product in queryset:
                url = f"https://{ALLEGRO_API_URL}/sale/offers?external.id={product.sku}&publication.status=ACTIVE"
                offers = allegro_request('GET', url, vendor.name, headers=headers)
                print('allegro_update offers ----------------', offers)
                for offer in offers.json()['offers']:
                    edit_url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{offer['id']}"
                    self.create_offer_from_product(request, 'PATCH', product, edit_url, access_token, vendor.name, producer=None)
    
    allegro_update.short_description = "📝 Aktualizuj oferty do Allegro"



    def allegro_export(self, request, queryset):

        # print('allegro_export request.user ----------------', request.user)
        url = f"https://{ALLEGRO_API_URL}/sale/product-offers"
        vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl')
        # for vendor in vendors:
        #     print('allegro_export vendors ----------------', vendors)

        for vendor in vendors:
            # print('check vendor ----------------', vendor)
            access_token = vendor.access_token
            producer = self.responsible_producers(access_token, vendor.name)
            # print('allegro_export producer ----------------', producer)
        
            for product in queryset:
               product_vendors = product.vendors.all()
               if vendor in product_vendors:
               #     print('if vendor in product_vendors ----------------', vendor)
                   self.create_offer_from_product(request, 'POST', product, url, access_token, vendor.name, producer)
                # print('allegro_export vendors ----------------', product_vendors)
            #     print('allegro_export ----------------', product.ean)
                #  self.create_offer_from_product(request, product, url, access_token, vendor.name, producer)
    allegro_export.short_description = "🔄 Eksportuj oferty do Allegro"



    def responsible_producers(self, access_token, name):

        url = f"https://{ALLEGRO_API_URL}/sale/responsible-producers" 

        headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Authorization': f'Bearer {access_token}'
        }

        # response = requests.request("GET", url, headers=headers)

        response = allegro_request("GET", url, name, headers=headers) # params={"limit": 10}
        
        # print('create_offer_from_product response ----------------', response.text)
        return response.json()


    def create_offer_from_product(self, request, method, product, url, access_token, vendor_name, producer):

        # print('create_offer_from_product producer ----------------', producer["responsibleProducers"][0]['id'])
        # print('create_offer_from_product method ----------------', method)

        try:

            if method == "PATCH":
                payload = json.dumps({
                    "name": f"{product.title}",
                    "external": {
                        "id": f"{product.sku}" 
                    },
                    "productSet": [
                        {
                        "product": {
                            "id": product.ean,
                            "idType": "GTIN"
                        },
                        # "responsibleProducer": {
                        #     "type": "ID",
                        #     "id": producer["responsibleProducers"][0]['id']
                        # },
                        },
                    ],
                    "sellingMode": {
                        "price": {
                        # "amount": str(product.price),
                        "amount": str(
                            (product.price * (1 + product.tax_rate / 100)).quantize(
                                Decimal("0.01"), rounding=ROUND_HALF_UP
                            )
                        ),
                        "currency": "PLN"
                        }
                    },
                    "stock": {
                        "available": product.stock_qty
                    },
                    # 'delivery': {
                    #     'shippingRates': {
                    #         'name': 'Paczkomat 1szt'
                    #     }
                    # },
                })

            else:   
                payload = json.dumps({
                    "name": f"{product.title}",
                    "external": {
                        "id": f"{product.sku}" 
                    },
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
                        "amount": str(product.price),
                        "currency": "PLN"
                        }
                    },
                    "stock": {
                        "available": product.stock_qty
                    },
                    'delivery': {
                        'shippingRates': {
                            'name': 'Paczkomat 1szt'
                        }
                    },
                })

            headers = {
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json',
                'Accept-Language': 'pl-PL',
                'Authorization': f'Bearer {access_token}'
            }

            # response = requests.request("POST", url, headers=headers, data=payload)
            response = allegro_request(method, url, vendor_name, headers=headers, data=payload)
            # print(f'create_offer_from_product {method} response ----------------', response)
            # print(f'create_offer_from_product {method} response text ----------------', response.text)
            if response.status_code == 200:
                    self.message_user(request, f"✅ Zmieniłęs ofertę {product.sku} allegro dla {vendor_name}", level='success')
            if response.status_code == 202:
                    self.message_user(request, f"✅ Wystawiłeś ofertę {product.sku} allegro dla {vendor_name}", level='success')
            elif response.status_code == 401:
                self.message_user(request, f"⚠️ Nie jesteś załogowany {vendor_name}", level='error')
            else:
                self.message_user(request, f"EAN:{product.ean}; SKU: {product.sku} - {response.status_code} - {response.text} dla {vendor_name}", level='info')
            return response
        except requests.exceptions.HTTPError as err:
            self.message_user(request, f"⚠️ EAN:{product.ean}; SKU: {product.sku} - {err} dla {vendor_name}", level='error')
            raise SystemExit(err)
       

    def get_me(self, access_token, name):

        url = f"https://{ALLEGRO_API_URL}/me"

        headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Authorization': f'Bearer {access_token}'
        }

        response = allegro_request("GET", url, name, headers=headers)
        return response


    def allegro_price_change(self, request, access_token, vendor_name, offer_id, new_price):

        try:
            url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"

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

            # response = requests.patch(url, headers=headers, data=json.dumps(payload))
            response = allegro_request("PATCH", url, vendor_name, headers=headers, data=json.dumps(payload))
            # print('allegro_price_change response ----------------', response.text)

        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        

    def allegro_stock_change(self, request, access_token, vendor_name, offer_id, quantity):

        try:
            url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"

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

            # response = requests.patch(url, headers=headers, data=json.dumps(payload))
            response = allegro_request("PATCH", url, vendor_name, headers=headers, data=json.dumps(payload))
            # print('allegro_price_change response ----------------', response.text)

            if response.status_code == 200:
                self.message_user(
                    request,
                    f"✅ Konto {vendor_name}; Ilość została poprawnie zmieniona (offer {offer_id})",
                    level="success"
                )
            else:
                # parse Allegro error response
                errors = response.json().get("errors", [])
                for err in errors:
                    self.message_user(
                        request,
                        f"⚠️ Błąd edycji ilości dla konta {vendor_name} (oferta {offer_id}): {err.get('userMessage')}",
                        level="error"
                    )

        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        

    def allegro_title_change(self, request, access_token, vendor_name, offer_id, title):

        try:
            url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"

            payload = {
                "name": title,
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.allegro.public.v1+json",
                "Content-Type": "application/vnd.allegro.public.v1+json"
            }

            # response = requests.patch(url, headers=headers, data=json.dumps(payload))
            response = allegro_request("PATCH", url, vendor_name, headers=headers, data=json.dumps(payload))
            print('allegro_title_change response ----------------', response)
            print('allegro_title_change response ----------------', response.text)

            if response.status_code == 200:
                self.message_user(
                    request,
                    f"✅ Konto {vendor_name}; Tytuł oferty został poprawnie zmieniony (offer {offer_id})",
                    level="success"
                )
            else:
                # parse Allegro error response
                errors = response.json().get("errors", [])
                for err in errors:
                    self.message_user(
                        request,
                        f"⚠️ Błąd edycji tytułu dla konta {vendor_name} (oferta {offer_id}): {err.get('userMessage')}",
                        level="error"
                    )

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


# @admin.register(AllegroOrderItemInline)
class AllegroOrderItemInline(admin.TabularInline):
    model = AllegroOrderItem
    extra = 0  # nie pokazuj pustych wierszy na start
    fields = ("product", "offer_name", "quantity", "price_amount", "price_currency")


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    fields = ['invoice_number', 'created_at', 'is_generated', 'sent_to_buyer']
    readonly_fields = ['invoice_number', 'created_at', 'is_generated', 'sent_to_buyer']
    can_delete = False


class InvoiceFileInline(admin.TabularInline):
    model = InvoiceFile
    extra = 0
    readonly_fields = ("invoice_number_display", "created_at")
    fields = ("invoice_number_display", "created_at")

    def invoice_number_display(self, obj):
        if obj.invoice:
            return format_html(
                '<a href="{}" target="_blank">Pobierz: {}</a>',
                obj.file.url,
                obj.invoice.invoice_number
            )
        elif obj.invoice_correction:
            return format_html(
                '<a href="{}" target="_blank">Pobierz korektę: {}</a>',
                obj.file.url,
                obj.invoice_correction.invoice_number
            )
        return "-"
    invoice_number_display.short_description = "Faktura / Korekta"



class InvoiceCorrectionInline(admin.TabularInline):
    model = InvoiceCorrection
    extra = 0
    fields = ['invoice_number', 'created_at', 'is_generated', 'sent_to_buyer']
    readonly_fields = ['invoice_number', 'created_at', 'is_generated', 'sent_to_buyer']
    can_delete = False



@admin.register(AllegroOrder)
class AllegroOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'invoice_generated', 'vendor', 'buyer_login', 'occurred_at', 'get_type_display_pl']
    list_filter = ['vendor', 'invoice_generated', 'type', 'occurred_at',]
    search_fields = ['order_id', 'buyer_login', 'buyer_email', 'get_type_display_pl']
    actions = ['generate_invoice', 'remove_duplicate_invoices']
    inlines = [AllegroOrderItemInline, InvoiceInline, InvoiceCorrectionInline]

    change_list_template = "admin/store/allegroorder/change_list.html"

    invoice_required = None
    invoice_data = {}

    def get_type_display_pl(self, obj):
        mapping = {
            'READY_FOR_PROCESSING': 'Gotowe do realizacji',
            'BOUGHT': 'Zakupione',
            'FILLED_IN': 'Uzupełnione dane kupującego',
        }
        return mapping.get(obj.type, obj.type)
    get_type_display_pl.short_description = "Typ zdarzenia"
    
    def get_buyer_info(self, order_id, access_token, vendor_name):

        try:
            url = f"https://{ALLEGRO_API_URL}/order/checkout-forms/{order_id}"
            headers = {
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Authorization': f'Bearer {access_token}'
            }
            # response = requests.get(url, headers=headers)
            response = allegro_request("GET", url, vendor_name, headers=headers)
            # print('Fetching order buyer_info ----------------', response, response.text)
            return response.json()
        except Exception as e:
                print(f"Error fetching orders for {order_id}: {e}")



    def fetch_and_store_allegro_orders(self, request, queryset=None):
        vendors = Vendor.objects.filter(marketplace='allegro.pl')

        for vendor in vendors:
            try:
                url = f"https://{ALLEGRO_API_URL}/order/events"
                headers = {
                    'Accept': 'application/vnd.allegro.public.v1+json',
                    'Authorization': f'Bearer {vendor.access_token}'
                }
                # response = requests.get(url, headers=headers)
                response = allegro_request("GET", url, vendor.name, headers=headers)

                if response.status_code == 200:
                    self.message_user(request, f"✅ Pobrano zamówienia allegro dla {vendor.name}", level='success')
                elif response.status_code == 401:
                    self.message_user(request, f"⚠️ Nieprawidłowy token dostępu dla {vendor.name}", level='error')
                    continue

                events = response.json().get('events', [])

                for event in events:
                    # print('Processing event ----------------', event)
                    order = event.get('order') or {}
                    checkout_form = order.get('checkoutForm') or {}
                    checkout_form_id = checkout_form.get('id')
                    if not checkout_form_id:
                        continue

                    buyer_info = self.get_buyer_info(checkout_form_id, vendor.access_token, vendor.name) or {}
                    buyer = buyer_info.get('buyer') or {}
                    invoice = buyer_info.get('invoice') or {}
                    address = invoice.get('address') or {}
                    company = address.get('company') or {}
                    ids = company.get('ids') or []
                    buyer_nip = ids[0].get('value') if ids else 'brak'

                    line_items = order.get('lineItems') or []

                    delivery = buyer_info.get('delivery') or {}
                    delivery_cost = float(delivery.get('cost', {}).get('amount', 0))
                    is_smart = delivery.get('smart')

                    # print('buyer_info delivery ----------------', delivery)
                    # print('buyer_info delivery_cost ----------------', delivery_cost)
                    # print('buyer_info is_smart ----------------', is_smart)


                    # print('company ----------------', company.get('name', ''))
                    # print('buyer_zipcode ----------------', buyer.get('address', {}).get('postCode', ''))

                    delivery_cost = float(buyer_info['delivery']['cost']['amount']) or 0.00
                    is_smart = buyer_info.get('delivery', {}).get('smart')

                    # --- 1. Utwórz/aktualizuj nagłówek zamówienia ---
                    allegro_order, created = AllegroOrder.objects.update_or_create(
                        event_id=event['id'],
                        order_id=checkout_form_id,
                        vendor=vendor,
                        defaults={
                            'buyer_login': buyer.get('login', ''),
                            'buyer_email': buyer.get('email', ''),
                            'buyer_name': f'{buyer.get("firstName", "")} {buyer.get("lastName", "")}',
                            'buyer_company_name': buyer.get("companyName", ""),
                            'buyer_street': buyer.get('address', {}).get('street', ''),
                            'buyer_zipcode': buyer.get('address', {}).get('postCode', ''),
                            'buyer_city': buyer.get('address', {}).get('city', ''),
                            'buyer_nip': buyer_nip,
                            'occurred_at': parse_datetime(event['occurredAt']),
                            'type': event['type'],
                            'is_smart': is_smart,
                            'delivery_cost': 0 if is_smart else delivery_cost,
                        }
                    )

                    # --- 2. Utwórz/aktualizuj pozycje zamówienia ---
                    for item in line_items:
                        external_id = item['offer'].get('external', {}).get('id')
                        offer_name = item['offer']['name']
                        price = Decimal(item['price']['amount'])
                        quantity = item['quantity']
                        product = Product.objects.filter(sku=external_id).first()


                        # Tworzenie produktu w www sklepie jeśli go tam nie ma
                        # w przypadku gdy był wystawiony tylko na all-ro
                        product, _ = Product.objects.get_or_create(
                            sku=external_id,

                        )
                        product.title=offer_name
                        product.save(update_fields=['title'])

                        AllegroOrderItem.objects.update_or_create(
                            order=allegro_order,
                            offer_id=item['offer']['id'],
                            defaults={
                                'product': product,
                                'offer_name': item['offer']['name'],
                                'quantity': item['quantity'],
                                'price_amount': item['price']['amount'],
                                'price_currency': item['price']['currency'],
                                'tax_rate': item.get('tax', {}).get('rate', 23.00),
                            }
                        )

                        # aktualizacja stanu magazynowego
                        if event['type'] == 'READY_FOR_PROCESSING':
                            if created and product:
                                product.stock_qty = max(product.stock_qty - item['quantity'], 0)
                                product.save(update_fields=['stock_qty'])
                                allegro_order.stock_updated = True
                                allegro_order.save(update_fields=['stock_updated'])
                                self.message_user(
                                    request,
                                    f"✅ Zaktualizowano stan magazynowy dla {product.sku}: -{item['quantity']} → {product.stock_qty}",
                                    level='success'
                                )

                    # --- 3. Faktura - auto generating ---
                    # if event['type'] == 'READY_FOR_PROCESSING':
                    #     invoice_required = invoice.get('required', False)
                    #     invoice_data = {
                    #         'created_at': now(),
                    #         'buyer_email': allegro_order.buyer_email,
                    #         'vendor': allegro_order.vendor,
                    #         'is_generated': True,
                    #     }

                    #     if invoice_required:
                    #         invoice_data.update({
                    #             'buyer_name': invoice.get('address', {}).get('company', {}).get('name', allegro_order.buyer_login),
                    #             'buyer_street': invoice.get('address', {}).get('street', ''),
                    #             'buyer_zipcode': invoice.get('address', {}).get('zipCode', ''),
                    #             'buyer_city': invoice.get('address', {}).get('city', ''),
                    #             'buyer_nip': invoice.get('address', {}).get('company', {}).get('ids', [{}])[0].get('value', 'brak'),
                    #         })
                    #     else:
                    #         invoice_data.update({
                    #             'buyer_name': allegro_order.buyer_login,
                    #             'buyer_street': buyer.get('address', {}).get('street', ''),
                    #             'buyer_zipcode': buyer.get('address', {}).get('postalCode', ''),
                    #             'buyer_city': buyer.get('address', {}).get('city', ''),
                    #             'buyer_nip': 'Brak',
                    #         })

                        # Invoice.objects.update_or_create(
                        #     allegro_order=allegro_order,
                        #     defaults=invoice_data
                        # )

            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Błąd pobierania zamówień dla {vendor.name}: {e}",
                    level='error'
                )


    @admin.action(description="🧾 Generuj faktury")
    def generate_invoice(self, request, queryset):
        invoices = queryset.filter(invoice_generated=False)
        success_count = 0
        error_count = 0

        # for i in invoices:
        #     print('generate_invoice ----------- test', i)

        for allegro_order in invoices:
            # print('######################## generate_invoice #######################', allegro_order)
            # print('Generating invoice order*buyer_email ----------------', allegro_order.buyer_email)
            try:
                invoice_data = {
                    'created_at': now(),
                    'buyer_email': allegro_order.buyer_email or '',
                    'vendor': allegro_order.vendor or '',
                    'is_generated': True,
                    'buyer_name': allegro_order.buyer_name or '',
                    'buyer_street': allegro_order.buyer_street or '',
                    'buyer_zipcode': allegro_order.buyer_zipcode or '',
                    'buyer_city': allegro_order.buyer_city or '',
                    'buyer_nip': allegro_order.buyer_nip or 'Brak',
                }

                Invoice.objects.update_or_create(
                    allegro_order=allegro_order,
                    defaults=invoice_data
                )

                allegro_order.invoice_generated = True
                allegro_order.save(update_fields=['invoice_generated'])
                success_count += 1

            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"❌ Błąd przy generowaniu faktury dla zamówienia {allegro_order.order_id}: {e}",
                    level="error"
                )

        if success_count:
            # invoice.allegro_order.invoice_generated = True
            self.message_user(
                request,
                f"✅ Wygenerowano {success_count} faktur.",
                level='success'
            )
        if error_count:
            self.message_user(
                request,
                f"⚠️ {error_count} faktur nie udało się wygenerować.",
                level="warning"
            )



    
    def remove_duplicate_invoices(modeladmin, request, queryset):
        dupes = (
            Invoice.objects.values('allegro_order')
            .annotate(count=models.Count('id'))
            .filter(count__gt=1)
        )

        total_deleted = 0
        for d in dupes:
            invoices = Invoice.objects.filter(allegro_order=d['allegro_order']).order_by('id')
            to_delete = list(invoices[1:])  # zamieniamy na listę
            for inv in to_delete:
                inv.delete()
            total_deleted += len(to_delete)

        if total_deleted == 0:
            modeladmin.message_user(request, "✅ Brak duplikatów faktur do usunięcia.")
        else:
            modeladmin.message_user(request, f"🗑 Usunięto {total_deleted} zdublowanych faktur.")


    remove_duplicate_invoices.short_description = "🧹 Usuń zdublowane faktury"


# @admin.register(InvoiceCorrection)
# class InvoiceCorrectioneAdmin(admin.ModelAdmin):
#     inlines = [InvoiceInline]


# @admin.register(InvoiceFile)
class InvoiceFileAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'PDF Pliki',
            {
                'fields': ('order', 'created_at', 'file')
            },
        ),
    )

    readonly_fields = ('order', 'created_at', 'file')
    list_display = ('order', 'created_at', 'file')




class InvoiceCorrectionForm(forms.Form):
    # dynamicznie dodamy pola dla produktów
    pass


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Faktura', {
            'fields': ('invoice_number', 'allegro_order', 'shop_order', 'created_at', 'sent_to_buyer', 'corrected')
        }),
        ('Kupujący', {
            'fields': ('buyer_name', 'buyer_email', 'buyer_street', 'buyer_zipcode', 'buyer_city', 'buyer_nip')
        }),
        ('Zamówienie', {
            'fields': ('vendor', 'order_items_display', 'delivery_cost_display', 'order_date')
        }),
    )

    readonly_fields = (
        'invoice_number', 'created_at', 'formatted_generated', 'corrected',
        'allegro_order', 'shop_order', 'order_items_display', 'delivery_cost_display', 'order_date',
    )

    list_display = ['invoice_number', 'is_generated', 'sent_to_buyer', 'buyer_name', 'vendor', 'created_at']
    search_fields = ['invoice_number', 'buyer_name', 'buyer_email', 'shop_order__oid',]
    list_filter = ['is_generated', 'sent_to_buyer', 'vendor', 'created_at']
    actions = ['print_invoice_pdf', 'generate_invoice', 'create_correction']
    inlines = [InvoiceCorrectionInline]


    def formatted_generated(self, obj):
        return localtime(obj.generated_at).strftime('%d-%m-%Y') if obj.generated_at else "—"
    formatted_generated.short_description = "Data wygenerowania"


    # def order_items_display(self, obj):
    #     items = obj.allegro_order.items.all()
    #     if not items:
    #         return "Brak pozycji"
    #     rows = format_html_join(
    #         '\n',
    #         "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
    #         (
    #             (item.offer_name, f"{item.price_amount:.2f} {item.price_currency}", item.quantity,
    #              f"{item.price_amount * item.quantity:.2f} {item.price_currency}")
    #             for item in items
    #         )
    #     )
    #     table = format_html(
    #         "<table style='border-collapse: collapse;'>"
    #         "<tr><th>Nazwa</th><th>Cena</th><th>Ilość</th><th>Suma</th></tr>{}</table>",
    #         rows
    #     )
    #     return table
    # order_items_display.short_description = "Produkty w zamówieniu:"


    def order_items_display(self, obj):
        # Spróbuj pobrać pozycje z allegro_order
        items = None
        if getattr(obj, "allegro_order", None):
            items = obj.allegro_order.items.all()

        # Jeśli brak allegro_order albo brak pozycji → spróbuj shop_order
        if not items:
            if getattr(obj, "shop_order", None):
                items = obj.shop_order.orderitem.all()

        # Jeśli nadal brak → zwróć komunikat
        if not items:
            return "Brak pozycji"

        # Renderuj tabelę
        rows = format_html_join(
            '\n',
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
            (
                (
                    getattr(item, "offer_name", getattr(item.product, "title", "")),
                    f"{getattr(item, 'price_amount', getattr(item, 'price', 0)):.2f} "
                    f"{getattr(item, 'price_currency', 'PLN')}",
                    getattr(item, "quantity", getattr(item, "qty", 0)),
                    f"{(getattr(item, 'price_amount', getattr(item, 'price', 0)) * getattr(item, 'quantity', getattr(item, 'qty', 0))):.2f} "
                    f"{getattr(item, 'price_currency', 'PLN')}"
                )
                for item in items
            )
        )

        table = format_html(
            "<table style='border-collapse: collapse;'>"
            "<tr><th>Nazwa</th><th>Cena</th><th>Ilość</th><th>Suma</th></tr>{}</table>",
            rows
        )
        return table

    order_items_display.short_description = "Produkty w zamówieniu:"



    def delivery_cost_display(self, obj):
        cost = obj.allegro_order.delivery_cost or 0
        return f"{cost:.2f} PLN"
    delivery_cost_display.short_description = "Koszt dostawy:"

    def order_date(self, obj):
        date = obj.allegro_order.occurred_at
        return f"{date}"
    order_date.short_description = "Data zamówienia:"


    @admin.action(description="🖨️ Drukuj faktury")
    def print_invoice_pdf(self, request, queryset):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for invoice in queryset:
                vendor = invoice.vendor
                user = request.user

                # Web store logic
                if vendor.marketplace == 'kidnetic.pl':
                    # print('KIDNETIC-------------------', vendor.marketplace)
                    buyer_info = {
                        'name': invoice.buyer_name,
                        'street': invoice.buyer_street,
                        'zipCode': invoice.buyer_zipcode,
                        'city': invoice.buyer_city,
                        'taxId': invoice.buyer_nip,
                    }
                    # produkty z pozycji zamówienia
                    products = []
                    for item in invoice.shop_order.orderitem.all():
                        products.append({
                            'offer': {'name': item.product.title},
                            'quantity': item.qty,
                            'is_smart': False, # invoice.allegro_order.is_smart,
                            'delivery_cost': invoice.shop_order.shipping_amount,
                            'tax_rate': item.tax_fee or 23,
                            'price': {
                                'amount': item.price,
                                'currency': item.sub_total,
                            }
                        })

                    pdf_content = generate_invoice_webstore(invoice, vendor, user, buyer_info, products)
                
                else:
                    print(f'{vendor.marketplace}-------------------')
                    # allegro logic
                    buyer_info = {
                        'name': invoice.buyer_name,
                        'street': invoice.buyer_street,
                        'zipCode': invoice.buyer_zipcode,
                        'city': invoice.buyer_city,
                        'taxId': invoice.buyer_nip,
                    }

                    # produkty z pozycji zamówienia
                    products = []
                    for item in invoice.allegro_order.items.all():
                        products.append({
                            'offer': {'name': item.offer_name},
                            'quantity': item.quantity,
                            'is_smart': invoice.allegro_order.is_smart,
                            'delivery_cost': invoice.allegro_order.delivery_cost,
                            'tax_rate': item.tax_rate or 23,
                            'price': {
                                'amount': item.price_amount,
                                'currency': item.price_currency,
                            }
                        })

                    # generowanie PDF
                    pdf_content = generate_invoice_allegro(invoice, vendor, user, buyer_info, products)

                # print('PDF PRODUCTS ---------------', products)

                # bezpieczna nazwa pliku (zamiana / na _)
                safe_invoice_number = invoice.invoice_number.replace("/", "_")
                zip_file.writestr(f"{safe_invoice_number}.pdf", pdf_content)

        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response['Content-Disposition'] = 'attachment; filename="faktury.zip"'
        return response        

    @admin.action(description="📧 Wyślij faktury do klienta")
    def generate_invoice(self, request, queryset):

        user = request.user

        for invoice in queryset:
            vendor = invoice.vendor

            # Web store logic
            if vendor.marketplace == 'kidnetic.pl':
                # print('KIDNETIC-------------------', vendor.marketplace)
                buyer_info = {
                    'name': invoice.buyer_name,
                    'street': invoice.buyer_street,
                    'zipCode': invoice.buyer_zipcode,
                    'city': invoice.buyer_city,
                    'taxId': invoice.buyer_nip,
                }
                # produkty z pozycji zamówienia
                products = []
                for item in invoice.shop_order.orderitem.all():
                    products.append({
                        'offer': {'name': item.product.title},
                        'quantity': item.qty,
                        'is_smart': False, # invoice.allegro_order.is_smart,
                        'delivery_cost': invoice.shop_order.shipping_amount,
                        'tax_rate': item.tax_fee or 23,
                        'price': {
                            'amount': item.price,
                            'currency': item.sub_total,
                        }
                    })

                pdf_content = generate_invoice_webstore(invoice, vendor, user, buyer_info, products)
                try:
                    # przypięcie do zamówienia sklepowego
                    order = invoice.shop_order  # zakładam, że Invoice ma FK do CartOrder
                    filename = f"invoice_{invoice.invoice_number}.pdf"
                    # order.invoice_pdf.save(filename, ContentFile(pdf_content), save=True)
                    invoice.sent_to_buyer = True
                    invoice.save(update_fields=['sent_to_buyer'])
                    InvoiceFile.objects.create(
                        order=invoice.shop_order,
                        file=ContentFile(pdf_content, f"invoice_{invoice.invoice_number}.pdf"),
                        invoice=invoice
                    )
                    self.message_user(request, f"Faktura {invoice.invoice_number} została poprawnie dolączona do zamówienia")
                except Exception as e:
                    self.message_user(
                        request,
                        f"❌ Błąd wysyłki faktury {invoice.invoice_number} do Allegro: {e}",
                        level='error'
                    )

            else:
                # dane kupującego
                buyer_info = {
                    'name': invoice.buyer_name,
                    'street': invoice.buyer_street,
                    'zipCode': invoice.buyer_zipcode,
                    'city': invoice.buyer_city,
                    'taxId': invoice.buyer_nip,
                }

                # produkty z pozycji zamówienia
                products = []
                for item in invoice.allegro_order.items.all():
                    products.append({
                        'offer': {
                            'name': item.offer_name,
                        },
                        'quantity': item.quantity,
                        'is_smart': invoice.allegro_order.is_smart,
                        'delivery_cost': invoice.allegro_order.delivery_cost,
                        'tax_rate': item.tax_rate or 23,
                        'price': {
                            'amount': item.price_amount,
                            'currency': item.price_currency,
                        }
                    })

                # generowanie PDF
                pdf_content = generate_invoice_allegro(invoice, vendor, user, buyer_info, products)

                try:
                    resp = post_invoice_to_allegro(invoice, pdf_content, False)
                    self.message_user(request, f"{resp}")
                except Exception as e:
                    self.message_user(
                        request,
                        f"❌ Błąd wysyłki faktury {invoice.invoice_number} do Allegro: {e}",
                        level='error'
                    )



    def create_correction(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Wybierz dokładnie jedną fakturę do korekty.", level="error")
            return
        invoice = queryset.first()
        # przekierowanie do custom view
        return redirect(f"{invoice.id}/correction/")

    create_correction.short_description = "Korekcja faktury"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("<int:invoice_id>/correction/", self.admin_site.admin_view(self.correction_view), name="invoice_correction"),
        ]
        return custom_urls + urls

    def correction_view(self, request, invoice_id):
        invoice = Invoice.objects.get(pk=invoice_id)
        try:
            products = invoice.allegro_order.items.all()
            transport_cost = invoice.allegro_order.delivery_cost
            source = "allegro"
        except AttributeError:
            products = invoice.shop_order.orderitem.all()
            transport_cost = invoice.shop_order.shipping_amount
            source = "shop"


        # dynamiczny formularz
        # class DynamicCorrectionForm(forms.Form):
        #     def __init__(self, *args, **kwargs):
        #         super().__init__(*args, **kwargs)
        #         for i, product in enumerate(products, start=1):
        #             self.fields[f"quantity_{i}"] = forms.IntegerField(
        #                 label=product.offer_name,
        #                 initial=product.quantity,
        #                 min_value=0
        #             )
        #         self.fields["transport_cost"] = forms.DecimalField(
        #             label="Koszt transportu",
        #             initial=transport_cost,
        #             min_value=0,
        #             decimal_places=2,
        #             max_digits=10,
        #         )

        class DynamicCorrectionForm(forms.Form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for i, product in enumerate(products, start=1):
                    if source == "allegro":
                        label = product.offer_name
                        initial_qty = product.quantity
                    else:
                        label = product.product.title
                        initial_qty = product.qty
                    self.fields[f"quantity_{i}"] = forms.IntegerField(
                        label=label,
                        initial=initial_qty,
                        min_value=0
                    )
                self.fields["transport_cost"] = forms.DecimalField(
                    label="Koszt transportu",
                    initial=transport_cost,
                    min_value=0,
                    decimal_places=2,
                    max_digits=10,
                )


        if request.method == "POST":
            form = DynamicCorrectionForm(request.POST)
            if form.is_valid():
                # corrected_products = []
                # for i, product in enumerate(products, start=1):
                #     new_qty = form.cleaned_data[f"quantity_{i}"]
                #     corrected_products.append({
                #         "offer_name": product.offer_name,
                #         "quantity": new_qty,
                #         "price_amount": product.price_amount,
                #         "price_currency": product.price_currency,
                #         "tax_rate": product.tax_rate,
                #     })
                corrected_products = []
                for i, product in enumerate(products, start=1):
                    new_qty = form.cleaned_data[f"quantity_{i}"]
                    if source == "allegro":
                        corrected_products.append({
                            "offer_name": product.offer_name,
                            "quantity": new_qty,
                            "price_amount": product.price_amount,
                            "price_currency": product.price_currency,
                            "tax_rate": product.tax_rate,
                        })
                    else:
                        corrected_products.append({
                            "offer_name": product.product.title,
                            "quantity": new_qty,
                            "price_amount": float(product.product.price),
                            "price_currency": "PLN",  # or derive from shop settings
                            "tax_rate": 23,           # or derive dynamically
                        })


                # dodaj transport jako osobną pozycję
                new_transport_cost = form.cleaned_data["transport_cost"]
                # if new_transport_cost and new_transport_cost > 0:
                corrected_products.append({
                    "offer_name": "Transport",
                    "quantity": 1,
                    "price_amount": float(new_transport_cost),
                    "price_currency": "PLN",
                    "tax_rate": 23,  # lub dynamicznie, jeśli masz różne stawki
                })

                if source == "allegro":
                    correction = InvoiceCorrection.objects.create(
                        main_invoice=invoice,
                        created_at=now(),
                        allegro_order=invoice.allegro_order,
                        vendor=invoice.vendor,
                        buyer_name=invoice.buyer_name,
                        buyer_email=invoice.buyer_email,
                        buyer_street=invoice.buyer_street,
                        buyer_zipcode=invoice.buyer_zipcode,
                        buyer_city=invoice.buyer_city,
                        buyer_nip=invoice.buyer_nip,
                        is_generated=True,
                    )
                else:
                    correction = InvoiceCorrection.objects.create(
                        main_invoice=invoice,
                        created_at=now(),
                        shop_order=invoice.shop_order,
                        vendor=invoice.vendor,
                        buyer_name=invoice.buyer_name,
                        buyer_email=invoice.buyer_email,
                        buyer_street=invoice.buyer_street,
                        buyer_zipcode=invoice.buyer_zipcode,
                        buyer_city=invoice.buyer_city,
                        buyer_nip=invoice.buyer_nip,
                        is_generated=True,
                    )

                correction.products = normalize_products_for_json(corrected_products)
                correction.save()


                invoice.corrected = True
                invoice.save(update_fields=['corrected'])

                self.message_user(request, f"Utworzono korektę faktury nr {correction.invoice_number}")
                return redirect("..")
        else:
            form = DynamicCorrectionForm()

        context = dict(
            self.admin_site.each_context(request),  # <-- to dodaje sidebar i wszystkie aplikacje
            form=form,
            invoice=invoice,
            title=f"Korekta faktury nr {invoice.invoice_number}",
        )
        return render(request, "admin/invoice_correction.html", context)


# @admin.register(InvoiceCorrection)
# class InvoiceCorrectionAdmin(admin.ModelAdmin):
#     fieldsets = (
#         ('Faktura', {
#             'fields': ('invoice_number', 'created_at', 'sent_to_buyer') #'allegro_order', 
#         }),
#         ('Kupujący', {
#             'fields': ('buyer_name', 'buyer_email', 'buyer_street', 'buyer_zipcode', 'buyer_city', 'buyer_nip')
#         }),
#         ('Zamówienie', {
#             'fields': ('vendor', 'order_items_display', 'delivery_cost_display')
#         }),
#     )

#     readonly_fields = (
#         'invoice_number', 'created_at',
#         'order_items_display', 'delivery_cost_display' # 'allegro_order', 
#     )

#     list_display = ['invoice_number', 'is_generated', 'sent_to_buyer', 'buyer_name', 'vendor', 'created_at']
#     search_fields = ['invoice_number', 'buyer_name', 'buyer_email']
#     list_filter = ['is_generated', 'sent_to_buyer', 'vendor', 'created_at']
#     actions = ['print_invoice_correction_pdf', 'generate_correction_invoice', ]  

#     @admin.action(description="🧾 Wyślij fakturę koregującą do klienta")
#     def generate_correction_invoice(self, request, queryset):
#         for invoice in queryset:
#             vendor = invoice.main_invoice.vendor
#             print('generate_correction_invoice vendor ----------------', vendor.address)

#             main_invoice_number = invoice.main_invoice.invoice_number

#             # dane kupującego
#             buyer_info = {
#                 'name': invoice.buyer_name,
#                 'street': invoice.buyer_street,
#                 'zipCode': invoice.buyer_zipcode,
#                 'city': invoice.buyer_city,
#                 'taxId': invoice.buyer_nip,
#             }

#             _main_invoice_products = []
#             main_invoice_products = invoice.main_invoice.allegro_order.items.all()

#             for item in main_invoice_products:  # invoice.products to lista dictów
#                 _main_invoice_products.append({
#                     'offer': {
#                         'name': item.offer_name,
#                     },
#                     'quantity': item.quantity,
#                     'is_smart': invoice.main_invoice.allegro_order.is_smart,
#                     'delivery_cost': invoice.main_invoice.allegro_order.delivery_cost,
#                     'tax_rate': item.tax_rate,
#                     'price': {
#                         'amount': item.price_amount,
#                         'currency': item.price_currency,
#                     }
#                 })



#             # produkty z pozycji zamówienia
#             products = []
#             # produkty z JSONField w korekcie
#             invoice_products = to_decimal_products(invoice.products)
#             print('invoice_products ----------------', invoice_products)
#             for item in invoice_products:  # invoice.products to lista dictów
#                 products.append({
#                     'offer': {
#                         'name': item['offer_name'],
#                     },
#                     'quantity': item['quantity'],
#                     'is_smart': invoice.main_invoice.allegro_order.is_smart,
#                     'delivery_cost': invoice.main_invoice.allegro_order.delivery_cost,
#                     'tax_rate': item.get('tax_rate', 23),
#                     'price': {
#                         'amount': item['price_amount'],
#                         'currency': item['price_currency'],
#                     }
#                 })

#             # generowanie PDF
#             pdf_content = generate_correction_invoice_allegro(invoice, buyer_info, products, _main_invoice_products)

#             # try:
#             resp = post_invoice_to_allegro(invoice, pdf_content, True)
#             self.message_user(request, f"{resp}")

@admin.register(InvoiceCorrection)
class InvoiceCorrectionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Faktura', {
            'fields': ('invoice_number', 'created_at', 'sent_to_buyer') #'allegro_order', 
        }),
        ('Kupujący', {
            'fields': ('buyer_name', 'buyer_email', 'buyer_street', 'buyer_zipcode', 'buyer_city', 'buyer_nip')
        }),
        ('Zamówienie', {
            'fields': ('vendor', 'order_items_display', 'delivery_cost_display')
        }),
    )

    readonly_fields = (
        'invoice_number', 'created_at',
        'order_items_display', 'delivery_cost_display' # 'allegro_order', 
    )

    list_display = ['invoice_number', 'is_generated', 'sent_to_buyer', 'buyer_name', 'vendor', 'created_at']
    search_fields = ['invoice_number', 'buyer_name', 'buyer_email']
    list_filter = ['is_generated', 'sent_to_buyer', 'vendor', 'created_at']
    actions = ['print_invoice_correction_pdf', 'generate_correction_invoice', ] 

    @admin.action(description="📧 Wyślij fakturę koregującą do klienta")
    def generate_correction_invoice(self, request, queryset):

        user = request.user

        """ W przypadku faktury korygującej sprawdzamy, czy główna faktura jest powiązana z Allegro czy Webstore
            i na tej podstawie NAJPIERW generujemy odpowiedni PDF i wysyłamy go do Allegro lub zapisujemy w systemie Webstore.,
            """
        for invoice in queryset:
            # print('---- generate_correction_invoice ----', invoice.invoice_number)
            vendor = invoice.main_invoice.vendor
            main_invoice_number = invoice.main_invoice.invoice_number

            # dane kupującego
            buyer_info = {
                'name': invoice.buyer_name,
                'street': invoice.buyer_street,
                'zipCode': invoice.buyer_zipcode,
                'city': invoice.buyer_city,
                'taxId': invoice.buyer_nip,
            }

            _main_invoice_products = []
            products = []

            if getattr(invoice.main_invoice, "allegro_order", None):
                # --- ALLEGRO ---
                main_invoice_products = invoice.main_invoice.allegro_order.items.all()
                for item in main_invoice_products:
                    _main_invoice_products.append({
                        'offer': {'name': item.offer_name},
                        'quantity': item.quantity,
                        'is_smart': invoice.main_invoice.allegro_order.is_smart,
                        'delivery_cost': invoice.main_invoice.allegro_order.delivery_cost,
                        'tax_rate': item.tax_rate,
                        'price': {
                            'amount': item.price_amount,
                            'currency': item.price_currency,
                        }
                    })

                invoice_products = to_decimal_products(invoice.products)
                for item in invoice_products:
                    products.append({
                        'offer': {'name': item['offer_name']},
                        'quantity': item['quantity'],
                        'is_smart': invoice.main_invoice.allegro_order.is_smart,
                        'delivery_cost': invoice.main_invoice.allegro_order.delivery_cost,
                        'tax_rate': item.get('tax_rate', 23),
                        'price': {
                            'amount': item['price_amount'],
                            'currency': item['price_currency'],
                        }
                    })


                pdf_content = generate_correction_invoice_allegro(
                    invoice, buyer_info, user, products, _main_invoice_products
                )
                resp = post_invoice_to_allegro(invoice, pdf_content, True)

            # SEND FV TO CUSTOMER FOR WEBSTORE
            elif getattr(invoice.main_invoice, "shop_order", None):
                print('KOREKTA WYŚLIJ WEBSTORE----------------')
                # --- WEBSTORE / CARTORDER ---
                main_invoice_products = invoice.main_invoice.shop_order.orderitem.all()
                for item in main_invoice_products:
                    _main_invoice_products.append({
                        'offer': {'name': item.product.title},
                        'quantity': item.qty,
                        'delivery_cost': invoice.main_invoice.shop_order.shipping_amount,
                        'tax_rate': 23,  # lub dynamicznie
                        'price': {
                            'amount': float(item.price),
                            'currency': "PLN",
                        }
                    })

                invoice_products = to_decimal_products(invoice.products)
                for item in invoice_products:
                    products.append({
                        'offer': {'name': item['offer_name']},
                        'quantity': item['quantity'],
                        'delivery_cost': invoice.main_invoice.shop_order.shipping_amount,
                        'tax_rate': item.get('tax_rate', 23),
                        'price': {
                            'amount': item['price_amount'],
                            'currency': item.get('price_currency', "PLN"),
                        }
                    })

                # tu zamiast generate_correction_invoice_allegro -> własny generator PDF dla webstore
                pdf_content = generate_correction_invoice_webstore(
                    invoice, buyer_info, user, products, _main_invoice_products
                )
                # np. zapis do FileField w InvoiceFile:
                InvoiceFile.objects.create(
                    order=invoice.main_invoice.shop_order,
                    invoice_correction=invoice,
                    file=ContentFile(pdf_content, f"correction_{invoice.invoice_number}.pdf")
                )
                invoice.sent_to_buyer = True
                invoice.save(update_fields=['sent_to_buyer'])
                resp = "Faktura korekta dla webstore wygenerowana i zapisana"

            else:
                resp = "Brak powiązanego zamówienia Allegro ani CartOrder"

            self.message_user(request, f"{resp}")


    from django.utils.html import format_html, format_html_join

    def order_items_display(self, obj):
        items = obj.products or []
        if not items:
            return "Brak pozycji"
        
        rows = format_html_join(
            '\n',
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
            (
                (item['offer_name'], f"{item['price_amount']:.2f} {item['price_currency']}", item['quantity'],
                 f"{item['price_amount'] * item['quantity']:.2f} {item['price_currency']}")
                for item in items
            )
        )
        table = format_html(
            "<table style='border-collapse: collapse;'>"
            "<tr><th>Nazwa</th><th>Cena</th><th>Ilość</th><th>Suma</th></tr>{}</table>",
            rows
        )

        return table

    order_items_display.short_description = "Produkty w zamówieniu"



    def delivery_cost_display(self, obj):
        cost = obj.main_invoice.allegro_order.delivery_cost or 0
        return f"{cost:.2f} PLN"
    delivery_cost_display.short_description = "Koszt dostawy"  


    @admin.action(description="🖨️ Drukuj faktury korygujące (ZIP)")
    def print_invoice_correction_pdf(self, request, queryset):

        user = request.user
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for invoice in queryset:
                vendor = invoice.main_invoice.vendor
                buyer_info = {
                    'name': invoice.buyer_name,
                    'street': invoice.buyer_street,
                    'zipCode': invoice.buyer_zipcode,
                    'city': invoice.buyer_city,
                    'taxId': invoice.buyer_nip,
                }

                _main_invoice_products = []
                products = []

                if getattr(invoice.main_invoice, "allegro_order", None):
                    # --- ALLEGRO ---
                    for item in invoice.main_invoice.allegro_order.items.all():
                        _main_invoice_products.append({
                            'offer': {'name': item.offer_name},
                            'quantity': item.quantity,
                            'is_smart': invoice.main_invoice.allegro_order.is_smart,
                            'delivery_cost': invoice.main_invoice.allegro_order.delivery_cost,
                            'tax_rate': item.tax_rate,
                            'price': {
                                'amount': item.price_amount,
                                'currency': item.price_currency,
                            }
                        })

                    for item in to_decimal_products(invoice.products):
                        products.append({
                            'offer': {'name': item['offer_name']},
                            'quantity': item['quantity'],
                            'is_smart': invoice.main_invoice.allegro_order.is_smart,
                            'delivery_cost': invoice.main_invoice.allegro_order.delivery_cost,
                            'tax_rate': item.get('tax_rate', 23),
                            'price': {
                                'amount': item['price_amount'],
                                'currency': item['price_currency'],
                            }
                        })

                    pdf_content = generate_correction_invoice_allegro(
                        invoice, buyer_info, user, products, _main_invoice_products
                    )

                elif getattr(invoice.main_invoice, "shop_order", None):
                    # --- WEBSTORE / CARTORDER ---
                    for item in invoice.main_invoice.shop_order.orderitem.all():
                        _main_invoice_products.append({
                            'offer': {'name': item.product.title},
                            'quantity': item.qty,
                            'delivery_cost': invoice.main_invoice.shop_order.shipping_amount,
                            'tax_rate': 23,
                            'price': {
                                'amount': float(item.price),
                                'currency': "PLN",
                            }
                        })

                    for item in to_decimal_products(invoice.products):
                        products.append({
                            'offer': {'name': item['offer_name']},
                            'quantity': item['quantity'],
                            'delivery_cost': invoice.main_invoice.shop_order.shipping_amount,
                            'tax_rate': item.get('tax_rate', 23),
                            'price': {
                                'amount': item['price_amount'],
                                'currency': item.get('price_currency', "PLN"),
                            }
                        })

                    pdf_content = generate_correction_invoice_webstore(
                        invoice, buyer_info, user, products, _main_invoice_products
                    )

                else:
                    # brak powiązanego zamówienia
                    continue

                # bezpieczna nazwa pliku (zamiana / na _)
                safe_invoice_number = invoice.invoice_number.replace("/", "_")
                zip_file.writestr(f"invoice_{safe_invoice_number}.pdf", pdf_content)

        response = HttpResponse(buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="faktury_korygujace.zip"'
        return response




    # @admin.action(description="🖨️ Drukuj faktury korygujące (ZIP)")
    # def print_invoice_correction_pdf(self, request, queryset):
    #     buffer = BytesIO()
    #     with zipfile.ZipFile(buffer, 'w') as zip_file:
    #         for invoice in queryset:
    #             vendor = invoice.main_invoice.vendor
    #             buyer_info = {
    #                 'name': invoice.buyer_name,
    #                 'street': invoice.buyer_street,
    #                 'zipCode': invoice.buyer_zipcode,
    #                 'city': invoice.buyer_city,
    #                 'taxId': invoice.buyer_nip,
    #             }

    #             # produkty z faktury głównej (przed korektą)
    #             _main_invoice_products = []
    #             for item in invoice.main_invoice.allegro_order.items.all():
    #                 _main_invoice_products.append({
    #                     'offer': {'name': item.offer_name},
    #                     'quantity': item.quantity,
    #                     'is_smart': invoice.main_invoice.allegro_order.is_smart,
    #                     'delivery_cost': invoice.main_invoice.allegro_order.delivery_cost,
    #                     'tax_rate': item.tax_rate,
    #                     'price': {
    #                         'amount': item.price_amount,
    #                         'currency': item.price_currency,
    #                     }
    #                 })

    #             # produkty po korekcie (z JSONField)
    #             products = []
    #             for item in to_decimal_products(invoice.products):
    #                 products.append({
    #                     'offer': {'name': item['offer_name']},
    #                     'quantity': item['quantity'],
    #                     'is_smart': invoice.main_invoice.allegro_order.is_smart,
    #                     'delivery_cost': invoice.main_invoice.allegro_order.delivery_cost,
    #                     'tax_rate': item.get('tax_rate', 23),
    #                     'price': {
    #                         'amount': item['price_amount'],
    #                         'currency': item['price_currency'],
    #                     }
    #                 })

    #             # generowanie PDF
    #             pdf_content = generate_correction_invoice_allegro(
    #                 invoice, buyer_info, products, _main_invoice_products
    #             )

    #             # bezpieczna nazwa pliku (zamiana / na _)
    #             safe_invoice_number = invoice.invoice_number.replace("/", "_")
    #             zip_file.writestr(f"invoice_{safe_invoice_number}.pdf", pdf_content)

    #     response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    #     response['Content-Disposition'] = 'attachment; filename="faktury_korygujace.zip"'
    #     return response





class CartOrderAdmin(ImportExportModelAdmin):

    inlines = [CartOrderItemsInlineAdmin]
    search_fields = ['oid', 'full_name', 'email', 'mobile', 'delivery']
    list_editable = ['order_status', 'payment_status', 'delivery_status', 'shipping_label']
    list_filter = ['payment_status', 'order_status', 'delivery_status', 'delivery']
    list_display = ['oid', 'payment_status', 'order_status', 'delivery', 'shipping_label', 'delivery_status', 'sub_total', 'shipping_amount', 'total', 'date']
    actions = ['generate_pdf_labels', 'generate_invoice_webstore', 'print_invoice_pdf_webstore']

    inlines = [CartOrderItemsInlineAdmin, InvoiceInline, InvoiceCorrectionInline, InvoiceFileInline]


    @admin.action(description="🧾Generuj faktury")
    def generate_invoice_webstore(self, request, queryset):
        invoices = queryset.filter(invoice_generated=False)
        web_vendor = Vendor.objects.get(
            user=request.user,
            marketplace='kidnetic.pl'
            )
        success_count = 0
        error_count = 0

        for web_order in invoices:
            # print('Generating invoice order*buyer_email ----------------', web_order.email)
            try:
                invoice_data = {
                    'created_at': now(),
                    'buyer_email': web_order.email or '',
                    'vendor': web_vendor or '',
                    'is_generated': True,
                    'buyer_name': web_order.full_name or '',
                    'buyer_street': f'{web_order.street} {web_order.number}' or '',
                    'buyer_zipcode': web_order.post_code or '',
                    'buyer_city': web_order.city or '',
                    'buyer_nip': web_order.buyer_nip or 'Brak',
                }

                # print('generate_invoice_webstore --------------- test', invoice_data)

                generated_invoice = Invoice.objects.update_or_create(
                    shop_order=web_order,
                    defaults=invoice_data
                )

                web_order.invoice_generated = True
                web_order.save(update_fields=['invoice_generated'])
                success_count += 1

            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"❌ Błąd przy generowaniu faktury dla zamówienia {web_order.order_id}: {e}",
                    level="error"
                )

        if success_count:
            # invoice.allegro_order.invoice_generated = True
            self.message_user(
                request,
                f"Wygenerowano {success_count} faktur(ę/y).",
                level='success'
            )
        if error_count:
            self.message_user(
                request,
                f"⚠️ {error_count} faktur nie udało się wygenerować.",
                level="warning"
            )


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
    list_filter = ['return_status', 'return_decision', 'return_reason', 'order__oid', 'date']
    list_display = ['order', 'refund_processed', 'product__sku', 'product_image', 'product', 'qty', 'product__price', 'return_reason', 'return_status', 'return_decision']
    actions = ['payu_return']

    @admin.action(description="💸 Zwrot kosztów")
    def payu_return(self, request, queryset):

        vendor = Vendor.objects.get(marketplace='kidnetic.pl')
        payu_order_id = queryset.first().order.payu_order_id
        amount = queryset.first().product.price * queryset.first().qty
    
        payu_url = f"{PAYU_API_URL}/orders/{payu_order_id}/refunds"
        # access_token = 'c86d4ab6-3628-4329-9894-02e4d05e9aa5'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {vendor.access_token}"
        }

        payload = {
            "refund": {
                "description": "Refund",
                "amount": to_grosze(amount),
            }
        }

        response = requests.post(payu_url, json=payload, headers=headers, allow_redirects=False)
        print('*****payu_return Response**********', response.status_code, response.text)
        print('*****payu_return json********', response.json())

        if response.status_code == 200:
            for item in queryset:
                item.refund_processed = True
                item.return_status = 'Koszty zwrócone Payu'
                item.save(update_fields=['refund_processed', 'return_status'])
            self.message_user(
                request,
                f"Zwrot środków w wysokości {amount} PLN został pomyślnie przetworzony w PayU.",
                level='success'
            )
        elif response.status_code == 401:
            new_access_token = payu_authenticate()
            if new_access_token:
                vendor.access_token = new_access_token
                vendor.save(update_fields=['access_token'])
                headers["Authorization"] = f"Bearer {new_access_token}"
                response = requests.post(payu_url, json=payload, headers=headers, allow_redirects=False)
                if response.status_code == 200:
                    print('*****RE-payu_return Response**********', response.status_code, response.text)
                    print('*****RE-payu_return json********', response.json())
                    for item in queryset:
                        item.refund_processed = True
                        item.return_status = 'Koszty zwrócone Payu'
                        item.save(update_fields=['refund_processed', 'return_status'])
                    self.message_user(
                        request,
                        f"Zwrot środków w wysokości {amount} PLN został pomyślnie przetworzony w PayU.",
                        level='success'
                    )
                else:
                    error_message = response.json().get('status', {}).get('statusDesc', 'Nieznany błąd podczas przetwarzania zwrotu w PayU.')
                    self.message_user(
                        request,
                        f"Nie udało się przetworzyć zwrotu środków w PayU: {error_message}",
                        level='error'
                    )
            
            else:
                self.message_user(
                    request,
                    "Nie udało się odświeżyć tokena dostępu PayU.",
                    level='error'
                )
        else:
            error_message = response.json().get('status', {}).get('statusDesc', 'Nieznany błąd podczas przetwarzania zwrotu w PayU.')
            self.message_user(
                request,
                f"Nie udało się przetworzyć zwrotu środków w PayU: {error_message}",
                level='error'
            )

            
        return response.json()

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
# admin.site.register(Review, ProductReviewAdmin)
admin.site.register(Category)
# admin.site.register(Gallery)
# admin.site.register(Tag, TagAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartOrderItem, CartOrderItemsAdmin)
admin.site.register(ReturnItem, ReturnItemAdmin)
# admin.site.register(Address, AddressAdmin)
# admin.site.register(Brand, BrandAdmin)
# admin.site.register(ProductFaq, ProductFaqAdmin)
# admin.site.register(Coupon, CouponAdmin)
# admin.site.register(Wishlist)
# admin.site.register(Notification, NotificationAdmin)
admin.site.register(DeliveryCouriers, DeliveryCouriersAdmin)
admin.site.register(ClientAccessLog, ClientAccessLogAdmin)
