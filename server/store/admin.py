import io
import time
from uuid import uuid4
from django.contrib import admin
from django.shortcuts import redirect, render
from django import forms
from django.db.models import F
from django.utils.timezone import now
from django.utils.html import format_html, format_html_join
from django.http import HttpResponse, JsonResponse
from django.utils.dateparse import parse_datetime
from django.urls import path
from django.forms import NumberInput

from bs4 import BeautifulSoup

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO, StringIO
import requests, json, csv
import zipfile
import os
import re
from html import escape
from dotenv import load_dotenv

from import_export.admin import ImportExportModelAdmin

from .allegro_views.delivery.dpd import dpd_delivery_info

from .allegro_views.create_label import create_label

from .allegro_views.create_shipment import create_shipment

from .utils.payu import payu_authenticate, to_grosze
from store.allegro_views.views import allegro_request, get_allegro_id
from store.utils.invoice import *
from store.utils.decimal import *
from store.models import *
from store.tasks import *

import aiohttp
import asyncio
import json
from decimal import Decimal, ROUND_HALF_UP


# Load variables from .env into environment
load_dotenv()

# Access them like normal environment variables
ALLEGRO_API_URL = os.getenv("ALLEGRO_API_URL")
PAYU_API_URL = os.getenv("PAYU_API_URL")
_marketplace = os.getenv("marketplace")


def dbg(label, value):
    """Pretty‑print any value safely, even if it's None or deeply nested."""
    import json

    try:
        pretty = json.dumps(value, indent=4, ensure_ascii=False)
    except Exception:
        pretty = str(value)

    print(f"\n===== DEBUG: {label} =====")
    print(pretty)
    print("====================================\n")



@admin.action(description="Dodaj 3zł") #How to add 20% to the title/description?
def apply_discount(modeladmin, request, queryset):
    # queryset.update(price=F('price') * 0.8) #20%
    queryset.update(price=F('price') + 3)

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

    # vendor = forms.ModelChoiceField(queryset=Vendor.objects.filter(user__is_staff=True))

    vendors = forms.ModelMultipleChoiceField(
        queryset=Vendor.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    

class AllegroStockFilter(admin.SimpleListFilter):
    title = '📦 Allegro asortyment'
    parameter_name = 'allegro_in_stock'

    def lookups(self, request, model_admin):
        return [
            ('true', '✅ Dostępne na Allegro'),
            ('false', '❌ Niedostępne na Allegro'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(allegro_in_stock=True)
        if self.value() == 'false':
            return queryset.filter(allegro_in_stock=False)
        return queryset
    

class AllegroVendorFilter(admin.SimpleListFilter):
    title = '🛒 Sprzedawca Allegro'
    parameter_name = 'allegro_vendor'

    def lookups(self, request, model_admin):
        vendors = Vendor.objects.filter(marketplace='allegro.pl')
        return [(vendor.name, vendor.name) for vendor in vendors]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(vendors__name=self.value())
        return queryset
    

class KecjaUpdatesFilter(admin.SimpleListFilter):
    title = '🔃 Aktualizacje'
    parameter_name = 'updates'

    def lookups(self, request, model_admin):
        return [
            ('true', '✅ Do aktualizacji'),
            ('false', '❌ Brak aktualizacji'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(updates=True)
        if self.value() == 'false':
            return queryset.filter(updates=False)
        return queryset



# class ProductAdmin(ImportExportModelAdmin):
class ProductAdmin(admin.ModelAdmin):

    save_on_top = True

    fieldsets = (
        ('Podstawowe informacje', {
            'fields': (
                'title', 'allegro_ids', 'sku', 'ean', 'image', 'thumbnail', 'img_links',
                'description', 'text_description', 'category', 'sub_cat', 'tags', 'brand'
            )
        }),
        ('Parametry', {
            'fields': (
                'weight', 'height', 'width', 'depth'
            )
        }),
        ('Sprzedawcy', {
            'fields': ('vendors',)
        }),
        ('Ceny i podatki', {
            'fields': (
                'price', 'price_brutto', 'hurt_price','new_hurt_price', 'prowizja_allegro',
                'zysk_pln', 'zysk_procent', 'tax_rate', 'reach_out',
                'old_price', 'shipping_amount', 'allegro_delivery_price'
            )
        }),
        ('Stan magazynowy', {
            'fields': ('stock_qty', 'in_stock')
        }),
        ('Status produktu', {
            'fields': ('status', 'type', 'allegro_status', 'allegro_in_stock')
        }),
        ('Flagi produktu', {
            'fields': ('featured', 'hot_deal', 'special_offer', 'digital', 'updates')
        }),
        ('Statystyki', {
            'fields': ('views', 'orders', 'saved', 'rating')
        }),
        ('Identyfikatory', {
            'fields': ('pid', 'slug', 'date')
        }),
    )

    # inlines = [ProductImagesAdmin, SpecificationAdmin, ColorAdmin, SizeAdmin]
    search_fields = ['title', 'price', 'slug', 'sku', 'ean']
    list_filter = [AllegroVendorFilter, AllegroStockFilter, KecjaUpdatesFilter]
    list_editable = ['title', 'ean', 'stock_qty', 'hot_deal', 'in_stock', 'price_brutto', 'zysk_after_payments', 'zysk_procent',]
    list_display = [
        'modified_hidden', 
        'sku', 
        'vendor_checkboxes', 
        'product_image', 
        'allegro_in_stock', 
        'allegro_status', 
        'in_stock', 
        'title',
        'title_warning', 
        'stock_qty', 
        'ean', 
        'price_brutto',
        'hurt_price',  
        'hurt_price_diff', 
        'hurt_price_diff_value',
        'prowizja_allegro', 
        'zysk_after_payments', 
        'zysk_procent', 'hot_deal'
        ]
    # exclude = ('vendors',) 
    actions = [
        apply_discount, 
        'generate_allegro_seo_titles',
        'allegro_export', 
        'allegro_update', 
        'sync_selected_allegro_offers_async', 
        "activate_allegro_products",
        # 'update_products_description',
        'calculate_allegro_fee',
        'calculate_zysk_after_payments', 
        ]
    inlines = [GalleryInline, SpecificationInline, SizeInline, ColorInline]
    list_per_page = 20
    # prepopulated_fields = {"slug": ("title", )}
    form = ProductAdminForm

    class Media:
        css = {
            "all": ("admin/css/custom_css/my.css",)
        }

        js = ("admin/js/my.js",)

    offers = []

    change_list_template = "admin/store/product/change_list_.html"

    ##### Highlight new_hurt_price if different from hurt_price ######

    def hurt_price_diff_value(self, obj):
        """Tylko do sortowania"""
        if not obj.new_hurt_price or obj.new_hurt_price == obj.hurt_price:
            diff = 0
            # Zwracamy wartość, ale ukrytą
            return format_html(
                '<span style="display:none;">{}</span>',
                diff
            )
        else:
            diff = float(obj.new_hurt_price - obj.hurt_price)
            return obj.new_hurt_price

    hurt_price_diff_value.short_description = "Nowa cena hurtowa"
    hurt_price_diff_value.admin_order_field = "new_hurt_price"



    def hurt_price_diff(self, obj):
        if not obj.new_hurt_price or obj.new_hurt_price == obj.hurt_price:
            return ""

        diff = obj.new_hurt_price - obj.hurt_price
        sign = "+" if diff > 0 else ""
        color = "red" if diff > 0 else "green"

        # formatowanie liczby przed format_html
        formatted_diff = f"{diff:.2f}"

        return format_html(
            '<span style="color:{}; font-weight:bold;">{}{}</span>',
            color,
            sign,
            formatted_diff,
        )

    hurt_price_diff.short_description = "Różnica hurtowa"



    @admin.action(description="📈 Zastosuj różnicę hurtową do ceny brutto")
    def apply_hurt_price_difference(modeladmin, request, queryset):
        updated = 0

        batch = AllegroProductBatch.objects.create(
            status="PENDING",
            total_products=len(queryset)
        )

        for product in queryset:
            # Pomijamy jeśli brak różnicy
            if not product.new_hurt_price or product.new_hurt_price == product.hurt_price:
                continue

            diff = product.new_hurt_price - product.hurt_price

            # Aktualizacja ceny brutto
            product.price_brutto = product.price_brutto + diff

            # Reset new_hurt_price
            product.new_hurt_price = 0

            product.save(update_fields=["price_brutto", "new_hurt_price"])
            updated += 1

            # aktualizacja batcha
            batch.total_products += 1 
            batch.save(update_fields=["processed_products", "total_products"])

            AllegroProductUpdateLog.objects.create(
                batch_id=batch.id,
                product=product,
                updates= [],
                success=f"Zaktualizowano product {product.sku}: Cena hurtowa zmienione o {diff}, nowa Cena detaliczna: {product.price_brutto}",
                error=f"Bład aktualizacji product {product.sku}",
            )

        return redirect(f"/api/store/admin/allegroupdatebatch/{batch.id}/status/")


    #### END Highlight new_hurt_price if different from hurt_price ######


    ###### Vendor checkboxes ######

    def vendor_checkboxes(self, obj):
        html = ""

        vendors = Vendor.objects.filter(marketplace="allegro.pl")  # lub dowolny filtr, ale BEZ requesta
        product_vendors = set(obj.vendors.all())

        for vendor in vendors:
            checked = "checked" if vendor in product_vendors else ""
            html += f"""
                <label style='display:flex; align-items:center; gap:4px;'>
                    <input type="checkbox" class="vendor-toggle"
                        data-product="{obj.id}"
                        data-vendor="{vendor.id}"
                        {checked}>
                    {vendor.name}
                </label>
            """

        return format_html(html)

    vendor_checkboxes.short_description = "Sprzedawcy"


    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("toggle-vendor/", self.admin_site.admin_view(self.toggle_vendor)),
        ]
        return custom + urls
    
    def toggle_vendor(self, request):
        product_id = request.POST.get("product_id")
        vendor_id = request.POST.get("vendor_id")
        checked = request.POST.get("checked") == "true"

        product = Product.objects.get(id=product_id)
        vendor = Vendor.objects.get(id=vendor_id)

        if checked:
            product.vendors.add(vendor)
        else:
            product.vendors.remove(vendor)

        return JsonResponse({"status": "ok"})

    ###### End Vendor checkboxes ######


    def modified_hidden(self, obj):
        return format_html(
            '<span style="display:block;">{}</span>',
            localtime(obj.modified).strftime("%Y-%m-%d %H:%M:%S"),
        )

    modified_hidden.admin_order_field = "modified"
    modified_hidden.short_description = ""


    def title_warning(self, obj):
        if len(obj.title or "") > 75:
            return format_html('<span style="color:red;">⚠️ {} znaków</span>', len(obj.title))
        return ""
    title_warning.short_description = ">75 znaków"


    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)

        # stock_qty (IntegerField)
        if db_field.name == "stock_qty":
            formfield.widget = NumberInput(attrs={
                "style": "width:60px; text-align:right;"
            })

        # price_brutto (DecimalField)
        if db_field.name == "price_brutto":
            formfield.widget = NumberInput(attrs={
                "style": "width:80px; text-align:right;"
            })

        # zysk_after_payments (DecimalField)
        if db_field.name == "zysk_after_payments":
            formfield.widget = NumberInput(attrs={
                "style": "width:80px; text-align:right;"
            })

        # zysk_procent (DecimalField)
        if db_field.name == "zysk_procent":
            formfield.widget = NumberInput(attrs={
                "style": "width:80px; text-align:right;"
            })

        return formfield




    def get_search_results(self, request, queryset, search_term):
        # obsługa wielu SKU oddzielonych przecinkami
        if "," in search_term:
            terms = [t.strip() for t in search_term.split(",")]
            queryset = queryset.filter(sku__in=terms)
            return queryset, False

        return super().get_search_results(request, queryset, search_term)


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


    def calculate_delivery_cost(self, cena_brutto: Decimal, przesylki: int = 1) -> Decimal:
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

    def calculate_allegro_fee(self, request, queryset):
        """
        Oblicza prowizję Allegro na podstawie ceny brutto.

        """
        print('check vendor ----------------', request.user)
        vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl',)
        # print('check vendor ----------------', vendors)

        for vendor in vendors:
            print('check vendor ----------------', vendor)
            access_token = vendor.access_token

            headers = {
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Authorization': f'Bearer {access_token}'
            }

            try:
                # products = Product.objects.filter()
                for p in queryset:
                # print(f' ################### "product_map" ################### ', {len(product_map)})
                    if p.allegro_in_stock == True:

                        allegro_id = get_allegro_id(vendor.name, p.allegro_ids)
                        url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{allegro_id}"
                        try:
                            offer_resp = allegro_request("GET", url, vendor.name, headers=headers)
                            offer = offer_resp.json()
                            print(f' ################### "offer" ################### ', offer)

                            # If offers is a dict with errors
                            if isinstance(offer, dict) and "errors" in offer:
                                self.message_user(request, f"⚠️ {offer['errors'][0]['message']}", level="error")
                                return

                            count = 0 

                            url = f"https://{ALLEGRO_API_URL}/pricing/offer-fee-preview" 
                            headers = {
                                'Accept': 'application/vnd.allegro.public.v1+json',
                                'Content-Type': 'application/vnd.allegro.public.v1+json',
                                'Authorization': f'Bearer {access_token}'
                            }

                            payload = {
                                "offer": {
                                    "id": offer.get("id"),
                                    "name": offer.get("name"),
                                    "category": {
                                        "id": offer.get("category", {}).get("id")
                                    },
                                    "parameters": offer.get("parameters", []),
                                    "images": offer.get("images", []),
                                    "description": offer.get("description", {}),
                                    "sellingMode": {
                                        "format": offer.get("sellingMode", {}).get("format"),
                                        "price": offer.get("sellingMode", {}).get("price"),
                                        "minimalPrice": offer.get("sellingMode", {}).get("minimalPrice"),
                                        "startingPrice": offer.get("sellingMode", {}).get("startingPrice"),
                                        "netPrice": offer.get("sellingMode", {}).get("netPrice"),
                                    },
                                    "stock": offer.get("stock", {}),
                                    "location": offer.get("location", {}),
                                    "delivery": offer.get("delivery", {}),
                                    "afterSalesServices": offer.get("afterSalesServices", {}),
                                    "payments": offer.get("payments", {}),
                                    "external": offer.get("external", {}),
                                    "fundraisingCampaign": offer.get("fundraisingCampaign"),
                                    "promotion": offer.get("promotion", {}),
                                    "publication": offer.get("publication", {}),
                                },
                                # "classifiedsPackages": {
                                #     "basePackage": {
                                #         "id": "e76d443b-c088-4da5-95f7-cc9aaf73bf7b"
                                #     },
                                #     "extraPackages": [
                                #         {
                                #             "id": "bff60277-b92e-46b6-98a4-439f830ac0a1",
                                #             "republish": False
                                #         }
                                #     ]
                                # },
                                "marketplaceId": "allegro-pl"
                            }
                            response = allegro_request("POST", url, vendor.name, headers=headers, json=payload)
                            data = response.json()
                            commissions = data.get("commissions", [])
                            if commissions:
                                fee = commissions[0].get("fee", {})
                                amount_str = fee.get("amount")
                                if amount_str:
                                    amount_decimal = Decimal(amount_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                                    p.prowizja_allegro = amount_decimal
                                    p.save(update_fields=["prowizja_allegro"])

                                    reach_out_value = (p.price_brutto * (p.reach_out / 100)).quantize(
                                            Decimal("0.01"), rounding=ROUND_HALF_UP
                                        )

                                    if p.price_brutto < (p.hurt_price + p.prowizja_allegro + reach_out_value + p.allegro_delivery_price + Decimal("5.00")):
                                        p.price_brutto = (p.price_brutto + p.prowizja_allegro + reach_out_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                                        p.save(update_fields=["price_brutto"])


                                    # oblicz koszt dostawy na podstawie price_brutto
                                    delivery_cost = self.calculate_delivery_cost(p.price_brutto, przesylki=1).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                                    p.allegro_delivery_price = delivery_cost
                                    p.save(update_fields=["allegro_delivery_price"]) 

                                    # oblicz zysk po uwzględnieniu prowizji i kosztów dostawy
                                    p.zysk_after_payments = (
                                        p.price_brutto
                                        - reach_out_value
                                        - p.hurt_price
                                        - p.prowizja_allegro
                                        - p.allegro_delivery_price
                                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                                    p.save(update_fields=["zysk_after_payments"])
                            print(f' ################### "offer allegro fee" ################### ', data)
                            self.message_user(request, f"✅ Prowizja Allegro obliczona dla produktu SKU: {p.sku}", level="success")
                        except Exception as e:
                            self.message_user(request, f"❌ Błąd zapytania: {str(e)}", level="error")

            except Exception as e:
                self.message_user(request, f"❌ Błąd zapytania: {str(e)}", level="error")

    calculate_allegro_fee.short_description = "🧮 Oblicz prowizję Allegro"


    def calculate_zysk_after_payments(self, request, queryset):

        for p in queryset:
            reach_out_value = (p.price_brutto * (p.reach_out / 100)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            p.zysk_after_payments = (
                p.price_brutto
                - reach_out_value
                - p.hurt_price
                - p.prowizja_allegro
                - p.allegro_delivery_price 
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            p.save(update_fields=["zysk_after_payments"])

            self.message_user(request, f"✅ Prowizja Allegro obliczona dla produktu SKU: {p.sku}", level="success")

    calculate_zysk_after_payments.short_description = "💰 Oblicz zysk po prowizji i dostawie"



    # Generate SEO titles for Allegro
    def generate_allegro_seo_titles(self, request, queryset):

        batch = SeoTitleBatch.objects.create(status="PENDING")
        product_ids = list(queryset.values_list("id", flat=True))

        batch.total_products = len(product_ids)
        batch.save(update_fields=["total_products"])

        orchestrate_seo_title_batch.delay(batch.id, product_ids)

        return redirect(f"/api/store/admin/seotitlebatch/{batch.id}/status/")

    generate_allegro_seo_titles.short_description = "🤖 Generuj SEO tytuły z AI"

    

    def fetch_all_offers(self, vendor_name, headers):

        statuses = ["ACTIVE", "INACTIVE", "ENDED", "NOT_LISTED"]
        all_offers = []

        for status in statuses:
            offset = 0
            while True:
                url = (
                    f"https://{ALLEGRO_API_URL}/sale/offers"
                    f"?limit=100&offset={offset}"
                    f"&publication.marketplace=allegro-pl"
                    f"&publication.status={status}"
                )
                response = allegro_request("GET", url, vendor_name, headers=headers)
                data = response.json()

                offers = data.get("offers", [])
                if not offers:
                    break

                all_offers.extend(offers)
                offset += 100

                total_count = data.get("totalCount")
                if total_count and offset >= total_count:
                    break
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
                product_map = {obj.sku: obj for obj in products}
                print(f' ################### "product_map" ################### ', {len(product_map)})

                offers = self.fetch_all_offers(vendor.name, headers)
                print(f' ################### "offers" ################### ', {len(offers)})

                # If offers is a dict with errors
                if isinstance(offers, dict) and "errors" in offers:
                    self.message_user(request, f"⚠️ {offers['errors'][0]['message']}", level="error")
                    return

                count = 0 

                for offer in offers:
                    print(f' ################### "offer" ################### ', offer)

                    id = offer.get("id")
                    external = offer.get("external")
                    if not external:
                        continue

                    sku = external.get("id")
                    status = offer.get("publication", {}).get("status")
                    product = product_map.get(sku)
                    print(f' ################### "id" ################### ', id)

                    if not product:
                        continue
                    
                    if status == "ACTIVE":
                        count += 1
                        # print(f' ################### "ACTIVE" ################### {sku} ----- ', product.sku)
                        product.title = offer.get("name", product.title)
    
                        entry = {"vendor": vendor.name, "product_id": id}

                        if entry not in product.allegro_ids:
                            product.allegro_ids.append(entry)

                        product.allegro_in_stock = True
                        price_brutto = Decimal(str(offer.get("sellingMode", {}).get("price", {}).get("amount", "0")))
                        price_netto = (price_brutto / Decimal("1.23")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                        product.price = price_netto
                        product.price_brutto = price_brutto
                        print(f' ################### "count" ################### ', count)
                    else:
                        product.allegro_in_stock = False

                    product.allegro_status = status
                    product.save(update_fields=["title", "allegro_ids", "allegro_in_stock", "allegro_status", "price", "price_brutto",])

                self.message_user(request, "Twoje oferty zostały zaktualizowane", level="success")

            except Exception as e:
                self.message_user(request, f"❌ Błąd zapytania: {str(e)}", level="error")

    sync_allegro_offers.short_description = "🔄 Synchronizuj z Allegro"


    def sync_selected_allegro_offers_async(self, request, queryset):
        product_ids = list(queryset.values_list("id", flat=True))

        batch = AllegroProductBatch.objects.create(
            status="PENDING",
            # total_products=len(product_ids)
        )

        from store.tasks import sync_selected_offers_task
        sync_selected_offers_task.delay(batch.id, product_ids, request.user.id)

        return redirect(f"/api/store/admin/allegroupdatebatch/{batch.id}/status/")

    sync_selected_allegro_offers_async.short_description = "🔄 Przenieś z Allegro (zaznaczone)"




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


    
    def activate_allegro_products(self, request, queryset):
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
                url = f"https://{ALLEGRO_API_URL}/sale/offers?external.id={product.sku}&publication.status=INACTIVE"
                offers = allegro_request('GET', url, vendor.name, headers=headers)
                print('allegro_update offers ----------------', offers)
                for offer in offers.json()['offers']:
                    edit_url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{offer['id']}"
                    self.create_offer_from_product(request, 'PATCH', product, edit_url, access_token, vendor.name, producer=None, action='activate')
    
    activate_allegro_products.short_description = "✅ Aktywuj oferty do Allegro"



    def allegro_update(self, request, queryset):

        batch = AllegroProductBatch.objects.create(status="PENDING")
        product_ids = list(queryset.values_list("id", flat=True))

        # batch.total_products = len(product_ids)
        # batch.save(update_fields=["total_products"])

        action = 'update_products'

        orchestrate_allegro_updates.delay(action, batch.id, product_ids, request.user.id)

        return redirect(f"/api/store/admin/allegroupdatebatch/{batch.id}/status/")
    
    allegro_update.short_description = "♻️ Aktualizuj oferty do Allegro"

    


    def allegro_export(self, request, queryset):

        batch = AllegroProductBatch.objects.create(status="PENDING")
        product_ids = list(queryset.values_list("id", flat=True))

        vendors = Vendor.objects.filter(user=request.user, marketplace="allegro.pl")
        for vendor in vendors:
            for product in queryset:
                product_vendors = product.vendors.all()
                if vendor in product.vendors.all():
                    batch.total_products += 1

        # batch.total_products = len(product_ids)
        batch.save(update_fields=["total_products"])

        action = "post_products"

        orchestrate_allegro_updates.delay(action, batch.id, product_ids, request.user.id)

        return redirect(f"/api/store/admin/allegroupdatebatch/{batch.id}/status/")
    
    allegro_export.short_description = "📤 Eksportuj oferty do Allegro"

    # def allegro_export(self, request, queryset):

    #     # print('allegro_export request.user ----------------', request.user)
    #     url = f"https://{ALLEGRO_API_URL}/sale/product-offers"
    #     vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl')
    #     # for vendor in vendors:
    #     #     print('allegro_export vendors ----------------', vendors)

    #     for vendor in vendors:
    #         # print('check vendor ----------------', vendor)
    #         access_token = vendor.access_token
    #         producer = self.responsible_producers(access_token, vendor.name)
    #         # print('allegro_export producer ----------------', producer)
        
    #         for product in queryset:
    #            product_vendors = product.vendors.all()
    #            if vendor in product_vendors:
    #            #     print('if vendor in product_vendors ----------------', vendor)
    #                resp = self.create_offer_from_product(request, 'POST', product, url, access_token, vendor.name, producer, action='create')
    #                if resp.status_code == 201:
    #                    product.allegro_in_stock = True
    #                    product.allegro_status = 'ACTIVE'
    #                    product.allegro_id = resp.json().get('id')
    #                    product.save(update_fields=['allegro_in_stock', 'allegro_status', 'allegro_id'])
    #            #
    #             # print('allegro_export vendors ----------------', product_vendors)
    #         #     print('allegro_export ----------------', product.ean)
    #             #  self.create_offer_from_product(request, product, url, access_token, vendor.name, producer)
    # allegro_export.short_description = "📤 Eksportuj oferty do Allegro"



    async def update_products_description(self, request, queryset):
        vendors = Vendor.objects.filter(marketplace='allegro.pl') #list(Vendor.objects.filter(user=request.user, marketplace='allegro.pl'))
        products = queryset #list(queryset)

        print("update_products_description -----------------:", vendors)

        tasks = []
        tasks_data = []
        for vendor in vendors:
            access_token = vendor.access_token
            producer = self.responsible_producers(access_token, vendor.name)

            for product in products:
                product_vendors = list(product.vendors.all())  # ORM call here, safe (sync)
                print("All PATCH product_vendors:+*****************", product_vendors)
                if vendor in product_vendors:
                    allegro_id = get_allegro_id(vendor.name, product.allegro_ids)
                    url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{allegro_id}"
                    # build plain dict with only primitive values
                    tasks_data.append({
                        "sku": product.sku,
                        "title": product.title,
                        "description": product.description,
                        "ean": product.ean,
                        "price": product.price_brutto,
                        "tax_rate": product.tax_rate,
                        "stock_qty": product.stock_qty,
                        "img_links": product.img_links,
                        "url": url,
                        "access_token": access_token,
                        "vendor_name": vendor.name,
                        "producer": producer,
                    })
                    print("All PATCH tasks_data:+*****************", tasks_data)
                    # tasks.append(asyncio.create_task(self._run_patch_tasks(request, tasks_data)))
        # print("All PATCH tasks_data:+*****************", tasks_data)
        results = asyncio.run(self._run_patch_tasks(request, tasks_data))
        # results = await asyncio.gather(*tasks)
        print("All PATCH results:", results)

    update_products_description.short_description = "📝 Edytuj opisy ofert"


    async def _run_patch_tasks(self, request, tasks_data):
        print("_run_patch_tasks CALLED:-----------------------", tasks_data)
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._patch_offer(session, data, request)
                for data in tasks_data
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)


    async def _patch_offer(self, session, data, request):
        print("_patch_offer CALLED:-------------------")
        safe_html = self.sanitize_allegro_description(data["description"])
        payload = json.dumps({
            "name": data["title"],
            "external": {"id": data["sku"]},
            "productSet": [{"product": {"id": data["ean"], "idType": "GTIN"}}],
            "sellingMode": {"price": {"amount": str(data["price"]), "currency": "PLN"}},
            "stock": {"available": data["stock_qty"]},
            "description": {"sections": [{"items": [{"type": "TEXT", "content": safe_html}]}]},
            "images": self.build_images(data["img_links"], data["vendor_name"])
        })
        headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Content-Type': 'application/vnd.allegro.public.v1+json',
            'Authorization': f'Bearer {data["access_token"]}'
        }

        async with session.patch(data["url"], headers=headers, data=payload) as response:
            text = await response.text()
            print(f'PATCH {data["sku"]} -> {response.status}')
            if response.status == 200:
                self.message_user(request, f"✅ Zmieniłeś ofertę {data['sku']} allegro dla {data['vendor_name']}", level='success')
            elif response.status == 202:
                self.message_user(request, f"✅ Zakończyłeś edytować ofertę {data['sku']} allegro dla {data['vendor_name']}", level='success')
            elif response.status == 401:
                self.message_user(request, f"⚠️ Nie jesteś zalogowany {data['vendor_name']}", level='error')
            return response.status




    

    # def update_products_description(self, request, queryset):

    #     # print('allegro_export request.user ----------------', request.user)
    #     vendors = Vendor.objects.filter(user=request.user, marketplace='allegro.pl')
    #     # for vendor in vendors:
    #     #     print('allegro_export vendors ----------------', vendors)

    #     for vendor in vendors:
    #         # print('check vendor ----------------', vendor)
    #         access_token = vendor.access_token
    #         producer = self.responsible_producers(access_token, vendor.name)
    #         # print('allegro_export producer ----------------', producer)
        
    #         for product in queryset:
    #            product_vendors = product.vendors.all()
    #            if vendor in product_vendors:
    #            #     print('if vendor in product_vendors ----------------', vendor)
    #                url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{product.allegro_id}"
    #                self.update_description(request, 'PATCH', product, url, access_token, vendor.name, producer)
    #             # print('allegro_export vendors ----------------', product_vendors)
    #         #     print('allegro_export ----------------', product.ean)
    #             #  self.create_offer_from_product(request, product, url, access_token, vendor.name, producer)
    # update_products_description.short_description = "📝Edytuj opisy ofert"



    # def convert_description_for_allegro(self, html: str) -> str:
    #     soup = BeautifulSoup(html, "html.parser")

    #     # usuń wszystkie style, klasy, atrybuty (zostaw tylko src dla <img>)
    #     for tag in soup.find_all(True):
    #         tag.attrs = {k: v for k, v in tag.attrs.items() if k == "src"}

    #     # usuń <div> (rozpakuj zawartość)
    #     for div in soup.find_all("div"):
    #         div.unwrap()

    #     # zamień <h1>/<h2> na <h2> (bez styli)
    #     for h in soup.find_all(["h1", "h2"]):
    #         new_h = soup.new_tag("h2")
    #         new_h.string = h.get_text(strip=True)
    #         h.replace_with(new_h)

    #     # zamień <table> na <ul><li>
    #     for table in soup.find_all("table"):
    #         ul = soup.new_tag("ul")
    #         for td in table.find_all("td"):
    #             text = td.get_text(strip=True)
    #             if text:
    #                 li = soup.new_tag("li")
    #                 li.string = text
    #                 ul.append(li)
    #         table.replace_with(ul)

    #     # upewnij się, że <img> są samozamykające
    #     for img in soup.find_all("img"):
    #         img.attrs = {"src": img.get("src")}
    #         # BeautifulSoup w trybie html.parser sam zamknie <img />

    #     # zamień <b> na <h2> (bo <b> nie jest dozwolone)
    #     for b in soup.find_all("b"):
    #         new_h = soup.new_tag("h2")
    #         new_h.string = b.get_text(strip=True)
    #         b.replace_with(new_h)

    #     # zamień <span> na <p>
    #     for span in soup.find_all("span"):
    #         new_p = soup.new_tag("p")
    #         new_p.string = span.get_text(strip=True)
    #         span.replace_with(new_p)

    #     return str(soup)


    def sanitize_allegro_description(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # usuń wszystkie style, klasy, atrybuty
        for tag in soup.find_all(True):
            tag.attrs = {}

        # usuń <div> (rozpakuj zawartość)
        for div in soup.find_all("div"):
            div.unwrap()

        # zamień <h1>/<h2> na <h2> (bez styli)
        for h in soup.find_all(["h1", "h2"]):
            new_h = soup.new_tag("h2")
            new_h.string = "⭐ " + h.get_text(strip=True)
            h.replace_with(new_h)

        # zamień <table> na <ul><li>
        for table in soup.find_all("table"):
            ul = soup.new_tag("ul")
            for td in table.find_all("td"):
                text = td.get_text(strip=True)
                if text:
                    li = soup.new_tag("li")
                    li.string = f"➡️ {text}"
                    ul.append(li)
            table.replace_with(ul)

        # usuń wszystkie <img>
        for img in soup.find_all("img"):
            img.decompose()


        # usuń wszystkie <br>
        for br in soup.find_all("br"):
            br.decompose()

        # zamień <b> na <h2> (bo <b> nie jest dozwolone)
        for b in soup.find_all("b"):
            new_h = soup.new_tag("h2")
            new_h.string = b.get_text(strip=True)
            b.replace_with(new_h)

        # zamień <span> na <p>
        for span in soup.find_all("span"):
            new_p = soup.new_tag("p")
            new_p.string = span.get_text(strip=True)
            span.replace_with(new_p)

        return str(soup)


    def upload_image(self, url, vendor_name):
        """
        Wysyła pojedynczy URL do Allegro i zwraca link z domeny a.allegroimg.pl
        """
        _url = f"https://{ALLEGRO_API_URL}/sale/images"

        headers = {
            "Accept": "application/vnd.allegro.public.v1+json",
            "Content-Type": "application/vnd.allegro.public.v1+json",
        }

        payload = {"url": url}

        # ważne: używaj json=payload zamiast data=payload
        response = allegro_request("POST", _url, vendor_name, headers=headers, json=payload)
        data = response.json()
        print('data ----------------', data)

        # Allegro zwraca {"location": "..."}
        # return {"url": data["location"]}
        return data["location"]


    def build_images(self, img_links, vendor_name):
        """
        Wysyła wszystkie linki z img_links do Allegro i zwraca listę obiektów { "url": ... }
        """
        uploaded = []
        for link in img_links:
            uploaded.append(self.upload_image(link, vendor_name))
        print('uploaded ----------------', uploaded)
        return uploaded



    # def update_description(self, request, method, product, url, access_token, vendor_name, producer):

    #     # print('create_offer_from_product producer ----------------', producer["responsibleProducers"][0]['id'])
    #     # print('self.build_images(product.img_links) ----------------', self.build_images(product.img_links))

    #     raw_html = product.description # your original HTML content
    #     safe_html = self.sanitize_allegro_description(raw_html)

    #     try:
    #         payload = json.dumps({
    #             "name": f"{product.title}",
    #             "external": {
    #                 "id": f"{product.sku}" 
    #             },
    #             "productSet": [
    #                 {
    #                 "product": {
    #                     "id": f"{product.ean}", #product.ean,
    #                     "idType": "GTIN"
    #                 },
    #                 # "responsibleProducer": {
    #                 #     "type": "ID",
    #                 #     "id": producer["responsibleProducers"][0]['id']
    #                 # },
    #                 },
    #             ],
    #             "sellingMode": {
    #                 "price": {
    #                 # "amount": str(product.price),
    #                 "amount": str(
    #                     (product.price * (1 + product.tax_rate / 100)).quantize(
    #                         Decimal("0.01"), rounding=ROUND_HALF_UP
    #                     )
    #                 ),
    #                 "currency": "PLN"
    #                 }
    #             },
    #             "stock": {
    #                 "available": product.stock_qty
    #             },
    #             # 'delivery': {
    #             #     'shippingRates': {
    #             #         'name': 'Paczkomat 1szt'
    #             #     }
    #             # },
    #             "description": {
    #                 "sections": [
    #                     {
    #                         "items": [
    #                             {
    #                                 "type": "TEXT",
    #                                 "content": safe_html #self.convert_description_for_allegro(product.description)
    #                             }
    #                         ]
    #                     }
    #                 ]
    #             },
    #             "images": self.build_images(product.img_links, vendor_name)
    #         })

    #         headers = {
    #             'Accept': 'application/vnd.allegro.public.v1+json',
    #             'Content-Type': 'application/vnd.allegro.public.v1+json',
    #             'Accept-Language': 'pl-PL',
    #             'Authorization': f'Bearer {access_token}'
    #         }

    #         # response = requests.request("POST", url, headers=headers, data=payload)
    #         response = allegro_request('PATCH', url, vendor_name, headers=headers, data=payload)
    #         print(f'update_offer_from_product {method} response ----------------', response)
    #         print(f'update_offer_from_product {method} response text ----------------', response.text)
    #         if response.status_code == 200:
    #             self.message_user(request, f"✅ Zmieniłęs ofertę {product.sku} allegro dla {vendor_name}", level='success')
    #         if response.status_code == 202:
    #             product.allegro_in_stock = True
    #             self.message_user(request, f"✅ Zakończyłeś edytować ofertę {product.sku} allegro dla {vendor_name}", level='success')
    #         elif response.status_code == 401:
    #             self.message_user(request, f"⚠️ Nie jesteś załogowany {vendor_name}", level='error')
    #         # else:
    #         #     self.message_user(request, f"EAN:{product.ean}; SKU: {product.sku} - {response.status_code} - {response.text} dla {vendor_name}", level='info')
    #         return response
    #     except requests.exceptions.HTTPError as err:
    #         self.message_user(request, f"⚠️ EAN:{product.ean}; SKU: {product.sku} - {err} dla {vendor_name}", level='error')
    #         raise SystemExit(err)

    

    def create_offer_from_product(self, request, method, product, url, access_token, vendor_name, producer, action=None):

        # print('create_offer_from_product producer ----------------', producer["responsibleProducers"][0]['id'])
        # print('self.build_images(product.img_links) ----------------', self.build_images(product.img_links))
        print('create_offer_from_product action ----------------', action)

        raw_html = product.description # your original HTML content
        safe_html = ''
        if raw_html is not None:
            safe_html = self.sanitize_allegro_description(raw_html)
        else:
            safe_html = product.text_description

        try:

            if method == "PATCH":
                if action == "stock_qty":
                    payload = json.dumps({
                        "stock": {
                            "available": product.stock_qty
                        }
                    })
                elif action == "price_brutto":
                    payload = json.dumps({
                        "sellingMode": {
                            "price": {
                            "amount": str(product.price_brutto),
                            "currency": "PLN"
                            }
                        }
                    })
                elif action == "title":
                     payload = json.dumps({
                        "name": f"{product.title}",
                    })
                elif action == "activate":
                    payload = json.dumps({
                        "publication": {
                            "status": "ACTIVE", 
                        },
                    })
                elif action == "deactivate":
                    payload = json.dumps({
                        "publication": {
                            "status": "INACTIVE", 
                        },
                    })
                elif action == "delivery":
                    payload = json.dumps({
                        'delivery': {
                            'shippingRates': {
                                'name': "Paczkomat 1szt" #'Paczkomat 1szt'
                            }
                        }
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
                                "id": f"{product.ean}", #product.ean,
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
                            "amount": str(product.price_brutto),
                            "currency": "PLN"
                            }
                        },
                        "stock": {
                            "available": product.stock_qty
                        },
                        # "publication": {
                        #     "status": "ACTIVE", 
                        # },
                        # 'delivery': {
                        #     'shippingRates': {
                        #         'name': 'Paczkomat 1szt'
                        #     }
                        # },
                        "description": {
                                "sections": [
                                    {
                                        "items": [
                                            {
                                                "type": "TEXT", 
                                                    "content": f"<p>{product.text_description}</p>" if safe_html == "" or safe_html is None else safe_html
                                            }
                                        ]
                                    }
                                ]
                            },  
                                   
                        "images": self.build_images(product.img_links, vendor_name) if product.img_links is not None else None
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
                            "id": f"{product.ean}", #product.ean,
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
                        "amount": str(product.price_brutto),
                        "currency": "PLN"
                        }
                    },
                    "stock": {
                        "available": product.stock_qty
                    },
                    'delivery': {
                        'shippingRates': {
                            'name': "Paczkomat 1szt" #'Paczkomat 1szt'
                        }
                    },
                    "description": {
                        "sections": [
                            {
                                "items": [
                                    {
                                        "type": "TEXT",
                                        "content": safe_html if safe_html != "" or safe_html is not None else product.text_description
                                    }
                                ]
                            }
                        ]
                    },
                    "images": self.build_images(product.img_links, vendor_name)
                })

            headers = {
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json',
                'Accept-Language': 'pl-PL',
                'Authorization': f'Bearer {access_token}'
            }

            # response = requests.request("POST", url, headers=headers, data=payload)
            response = allegro_request(method, url, vendor_name, headers=headers, data=payload)
            print(f'create_offer_from_product {method} response ----------------', response)
            print(f'create_offer_from_product {method} response text ----------------', response.text)
            actions = {
                'price_brutto': 'cenę',
                'stock_qty': 'stan magazynowy',
                'title': 'tytuł',
                'description': 'opis',
                'activate': 'aktywowanie',
                'deactivate': 'dezaktywowanie',
                'delivery': 'metodę dostawy',
                'other': 'ofertę',
            }
            if response.status_code == 200:
                product.updates = False
                product.save(update_fields=['updates'])
                self.message_user(request, f"✅ Zmieniłęs {actions[action]} w {product.sku} allegro dla {vendor_name}", level='success')
            if response.status_code == 202:
                product.allegro_in_stock = True
                self.message_user(request, f"✅ Wystawiłeś ofertę {product.sku} allegro dla {vendor_name}", level='success')
            elif response.status_code == 401:
                self.message_user(request, f"⚠️ Nie jesteś załogowany {vendor_name}", level='error')
            elif response.status_code == 422:
                self.message_user(request, f"EAN:{product.ean}; SKU: {product.sku} - {response.status_code} - {response.text} dla {vendor_name}", level='error')
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
    # list_editable = ['width', 'height', 'length', 'weight']
    list_display = ['name', 'width', 'height', 'length', 'weight']

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
    fields = ("product", "offer_name", "quantity", "price_amount", "price_currency",)


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
    list_display = ['order_id', 'delivery_method_name', 'error', 'label_tag', 'invoice_generated', 'message_sent', 'vendor', 'buyer_login', 'occurred_at', 'get_type_display_pl']
    list_filter = ['vendor', 'delivery_method_name', 'invoice_generated', 'type', 'occurred_at',]
    # search_fields = ['order_id', 'event_id', 'buyer_login', 'buyer_email', 'get_type_display_pl']
    search_fields = [
        'delivery_method_name',
        'order_id',            # search by Allegro order id
        'event_id',            # search by event id
        'buyer_login',
        'buyer_email',
        'vendor__name',
        'id',                  # internal PK, useful for exact searches
    ]
    actions = [
        'create_allegro_orders_',
        'remove_duplicate_invoices', 
        'send_auto_message', 
        'generate_invoice'
        ]
    inlines = [AllegroOrderItemInline, InvoiceInline, InvoiceCorrectionInline]

    change_list_template = "admin/store/allegroorder/change_list.html"

    invoice_required = None
    invoice_data = {}

    def label_tag(self, obj): 
        if obj.label_file and obj.label_file.name: 
            return "✅" 
        return "—"

    def changelist_view(self, request, extra_context=None):
        # If no filter is applied, redirect with default filter for READY_FOR_PROCESSING
        if 'type__exact' not in request.GET:
            return redirect(f"{request.path}?type__exact=READY_FOR_PROCESSING")
        return super().changelist_view(request, extra_context=extra_context)

    def get_type_display_pl(self, obj):
        mapping = {
            'READY_FOR_PROCESSING': 'Gotowe do realizacji',
            'BOUGHT': 'Zakupione',
            'BUYER_CANCELLED': 'Anulowane',
            'FILLED_IN': 'Uzupełnione dane kupującego',
            'FULLFILMENT_STATUS_CHANGED': 'Zmiana statusu',
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

            print(' ///////////////////////////// Fetching order buyer_info ////////////////////////////// ', response, response.text)
            return response.json()
        except Exception as e:
                print(f"Error fetching orders for {order_id}: {e}")


    # Zamówienia Allegro - utwórz etykiety
    def create_allegro_orders_(self, request, queryset):

        batch = AllegroBatch.objects.create(status="PENDING")

        order_ids = list(queryset.values_list("order_id", flat=True))

        orchestrate_allegro_labels.delay(batch.id, order_ids)

        # redirect do strony statusu 
        return redirect(f"/api/store/admin/allegrobatch/{batch.id}/status/")

    create_allegro_orders_.short_description = "📦 Utwórz etykiety Allegro"



    def create_allegro_orders(self, request, queryset):
        # Wymyślić dodawanie numeru przesyłki do zamówienia allegro i zmienić status
        # Przetestowac z dwoma i więcej różnymi produktami w zamówieniu
        vendors = Vendor.objects.filter(marketplace='allegro.pl')

        errors = set()

        zip_buffer = io.BytesIO() # in‑memory ZIP 
        zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)

        # for vendor in vendors:
        #     url = f"https://{ALLEGRO_API_URL}/shipment-management/delivery-services"

        #     headers = {
        #         'Accept': 'application/vnd.allegro.public.v1+json',
        #         'Authorization': f'Bearer {vendor.access_token}'
        #     }
        #     # response = requests.get(url, headers=headers)
        #     response = allegro_request("GET", url, vendor.name, headers=headers)
        #     # print('create_allegro_orders ######################## ', response, response.text)

        #     if response.status_code == 200:
                # self.message_user(request, f"✅ Pobrano zamówienia allegro dla {vendor.name}", level='success')


        for order in queryset:
            headers = {
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Authorization': f'Bearer {order.vendor.access_token}'
            }
            print('Processing order delivery_method_id  +3+3+3+3+3+3+3+3', order.delivery_method_id)
            if order.delivery_method_id is None:
                delivery_url = f"https://{ALLEGRO_API_URL}/order/checkout-forms/{order.order_id}"
                delivery = allegro_request("GET", delivery_url, order.vendor.name, headers=headers)
                delivery_method_id = (
                    delivery.json()
                    .get("delivery", {})
                    .get("method", {})
                    .get("id")
                )
                delivery_method_name = (
                    delivery.json()
                    .get("delivery", {})
                    .get("method", {})
                    .get("name")
                )
                pickup_point_id = (
                    delivery.json()
                    .get("delivery", {})
                    .get("pickupPoint", {})
                    .get("id")
                )
                pickup_point_name = delivery.json().get("delivery", {}).get("pickupPoint", {}).get("name")
                order.delivery_method_id = delivery_method_id
                order.delivery_method_name = delivery_method_name
                order.pickup_point_id = pickup_point_id
                order.pickup_point_name = pickup_point_name
                order.save(update_fields=['delivery_method_id', 'delivery_method_name', 'pickup_point_id', 'pickup_point_name'])

                print('Processing delivery ///////////////////', json.dumps(delivery.json(), indent=4, ensure_ascii=False))

            items = order.items.all()
            courier_name = " ".join(order.delivery_method_name.split()[-2:])
            courier = DeliveryCouriers.objects.filter(name__icontains=courier_name).first()
            if not courier:
                self.message_user(request, f"⚠️ Nie znaleziono kuriera {courier_name} dla zamówienia {order.order_id}", level='error')
                continue

            # 1. Combine items
            item_w = 0
            item_h = 0
            item_l = 0
            item_weight = 0
            item_volume = 0
            item_girth = 0
            max_w = float(courier.width or 0) 
            max_h = float(courier.height or 0) 
            max_l = float(courier.length or 0) 
            max_weight = float(courier.weight or 0) 
            max_volume = 0
            max_girth = 0
            
            max_packages = getattr(courier, "max_packages", 1) 
            if max_w != 0 and max_h != 0 and max_l != 0:
                max_volume = max_l + 2*max_w + 2*max_h
                max_girth = max_l + 2*max_w + 2*max_h
            # else:
            #     max_volume = item_l + 2*item_w + 2*item_h
            #     max_girth = item_l + 2*item_w + 2*item_h
            text_on_label = ""
            packages = [] 

            def check_girth(length, width, height):
                if length + 2*width + 2*height <= max_girth:
                    return True
                return False
            
            def check_volume(length, width, height):
                if length * width * height / 6000 <= max_volume:
                    return True
                return False

            val = []
            def get_max(value):
                val.append(value)
                return max(val)    
            
            for item in items:
                print(' _*__*__*__*__*__*_ Processing item _*__*__*__*__*__*_ ', item.product.sku, item.quantity)
                product = item.product 
                product_girth = check_girth(float(product.depth), float(product.width), float(product.height))
                product_volume = check_volume(float(product.depth), float(product.width), float(product.height))

                # if (float(product.depth)) >= max_l or float(product.width) >= max_w or float(product.height) >= max_h or float(product.weight) >= max_weight:
                #     order.error=f"❌ Produkt {product.sku} ma wymiary przekraczające maksymalne dla kuriera {courier.name} w zamówieniu {order.order_id}. Wymiary produktu: {product.depth}x{product.height}x{product.width} cm przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm."
                #     order.save(update_fields=['error'])
                #     self.message_user(request, f"❌ Produkt {product.sku} ma wymiary przekraczające maksymalne dla kuriera {courier.name} w zamówieniu {order.order_id}. Wymiary produktu: {product.depth}x{product.height}x{product.width} cm przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm.", level='error')
                #     continue
                #     # print(f"product dimensions exceed maximum for courier {product.sku} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                # if product_girth is False or product_volume is False:
                #     order.error=f"❌ Nie udało się skompletowac paczki w dopuszczalnych wymiarach dla zamówienia {order.order_id}. OBECNE Wymiary: {item_l}x{item_h}x{item_w} cm przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm."
                #     order.save(update_fields=['error'])
                #     self.message_user(request, f"❌ Nie udało się skompletowac paczki w dopuszczalnych wymiarach dla zamówienia {order.order_id}. OBECNE Wymiary: {item_l}x{item_h}x{item_w} cm przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm.", level='error')
                #     # print(f"product_girth is False or product_volume is False {product.sku} {product_girth}, {product_volume} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                #     continue

                item_w = get_max(float(product.width))
                item_h = get_max(float(product.height))
                item_l += float(product.depth) * item.quantity
                item_weight += float(product.weight) * item.quantity
                item_volume += item_l * item_w * item_h / 6000
                # Girth (DPD, UPS) 
                item_girth += item_l + 2 * item_w + 2 * item_h
                text_on_label += f"{item.quantity}x{item.product.sku}, "

                # Jeśli głębokość paczki przekracza maksymalną długość, spróbuj zwiększyć szerokość
                print(item_l, max_l,">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(item_w, max_w,">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(item_h, max_h,">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                if item_l >= max_l and item_w < max_w:
                    print(" item_l >= max_l and item_w < max_w OKAY >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    if max_w - item_w > float(product.depth):
                        print("max_w - item_w > float(product.depth) OKAY >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        item_w += item_l
                        item_l -= float(product.depth)
                        print(f"Udało się skompletowac paczke po szerokości w wymiarach: {item_w}x{item_h}x{item_l} cm @@#@#@#@#@#@#@#@#@#@#@#@#@#@#@")
                    elif max_h - item_h > float(product.depth):
                        print("max_h - item_h > float(product.depth) OKAY >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        item_h += item_l
                        item_l -= float(product.depth)
                        print(f"Udało się skompletowac paczke po wysokości a nie po szyrokości w wymiarach: {item_w}x{item_h}x{item_l} cm @@#@#@#@#@#@#@#@#@#@#@#@#@#@#@")

                elif item_l >= max_l and item_h < max_h:
                    print("item_l >= max_l and item_h < max_h OKAY >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    if max_h - item_h > float(product.depth):
                        print("max_h - item_h > float(product.depth) OKAY >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        item_h += item_l
                        item_l -= float(product.depth)
                        print(f"Udało się skompletowac paczke po wysokości w wymiarach: {item_w}x{item_h}x{item_l} cm @@#@#@#@#@#@#@#@#@#@#@#@#@#@#@")

                # else:
                #     print("Nie udało się skompletowac paczki w dopuszczalnych wymiarach >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                #     errors.add(f"❌ 1593 Nie udało się skompletowac paczki w dopuszczalnych wymiarach dla zamówienia {order.order_id}. OBECNE Wymiary: {item_l}x{item_h}x{item_w} cm przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm.")
                #     continue
                
                if order.delivery_method_name == "Allegro DPD Kurier":
                    packages = dpd_delivery_info(item_l, item_h, item_w, item_weight, item_volume, order, text_on_label)
                

                elif item_l < max_l and item_h < max_h and item_w < max_w and item_weight < max_w and item_volume < max_volume:
                    packages = [
                        {
                                "type":"PACKAGE",     # wymagane, typ przesyłki; dostępne wartości: PACKAGE (paczka), DOX (list), PALLET (przesyłka paletowa), OTHER (inna)
                                "length": {    # długość paczki
                                    "value":item_l,
                                    "unit":"CENTIMETER"
                                },
                                "width":{    # szerokość paczki
                                    "value":item_w,
                                    "unit":"CENTIMETER"
                                },
                                "height":{    # wysokość paczki
                                    "value":item_h,
                                    "unit":"CENTIMETER"
                                },
                                "weight":{    # waga paczki
                                    "value":item_weight,
                                    "unit":"KILOGRAMS"
                                },
                                "textOnLabel": text_on_label    # opis na etykiecie paczki
                            
                    }]
                    
                    print(f"*******************Zsumowano paczkę: Wymiary {item_l}x{item_h}x{item_w} cm, Waga: {item_weight} kg, Objętość: {item_volume} cm3 przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm ************************")
#@ ->
                # print(f"******************* ETAP PRZED PRZEKROCZENIEM: Wymiary {item_l}x{item_h}x{item_w} cm, Waga: {item_weight} kg, Objętość: {item_volume} cm3 przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm ************************")

                elif item_l >= max_l or item_h >= max_h or item_w >= max_w or item_weight > max_weight or item_volume > max_volume or item_girth > max_girth:

                    # order.error = f"❌ Przekroczono maksymalne wymiary lub wagę paczki dla zamówienia {order.order_id}. Maksymalne wymiary: {max_l}x{max_h}x{max_w} cm, maksymalna waga: {max_weight} kg. OBECNE WYMIARY I WAGA: {item_l}x{item_h}x{item_w} cm, {item_weight} kg."
                    # order.save(update_fields=['error'])
                    
                    # wymyślić logikę dodawania nastepnej paczki
                    print(f"____________Creating shipment dimension exceeded max ____________________ Wymiary {item_l}x{item_h}x{item_w} cm, Waga: {item_weight} kg")

                    re_packages = [
                        {
                                "type":"PACKAGE",     # wymagane, typ przesyłki; dostępne wartości: PACKAGE (paczka), DOX (list), PALLET (przesyłka paletowa), OTHER (inna)
                                "length": {    # długość paczki
                                    "value":float(item.product.depth),
                                    "unit":"CENTIMETER"
                                },
                                "width":{    # szerokość paczki
                                    "value":float(item.product.width),
                                    "unit":"CENTIMETER"
                                },
                                "height":{    # wysokość paczki
                                    "value":float(item.product.height),
                                    "unit":"CENTIMETER"
                                },
                                "weight":{    # waga paczki
                                    "value":float(item.product.weight),
                                    "unit":"KILOGRAMS"
                                },
                                "textOnLabel": f"{item.quantity}x{item.product.sku}"    # opis na etykiecie paczki
                            
                    }]

                    # Jeśli pojedynczy produkt przekracza dopuszczalne wymiary — NIE twórz przesyłki
                    if (
                        float(item.product.depth) >= max_l or
                        float(item.product.width) >= max_w or
                        float(item.product.height) >= max_h or
                        float(item.product.weight) > max_weight
                    ):
                        order.error = (
                            f"❌ Produkt {item.product.sku} przekracza dopuszczalne wymiary lub wagę.\n"
                            f"Maksymalne wymiary: {max_l}x{max_h}x{max_w} cm, max waga: {max_weight} kg.\n"
                            f"Wymiary produktu: {item.product.depth}x{item.product.height}x{item.product.width} cm, "
                            f"waga: {item.product.weight} kg."
                        )
                        order.save(update_fields=['error'])
                        print("❌ ______Produkt przekracza dopuszczalne wymiary — pomijam create_shipment_____")
                        continue

                    else:
                        order.error = ""
                        order.save(update_fields=['error'])


                    resp = create_shipment(ALLEGRO_API_URL, order.vendor, order, re_packages)
                    print('Creating shipment resp > ----------------', resp, resp.text)
                    if resp.status_code == 200 or resp.status_code == 201:
                        re_filename, _repdf_bytes = create_label(order, ALLEGRO_API_URL, resp, order.vendor, headers, errors, zip_file)
                        if re_filename and _repdf_bytes: 
                            zip_file.writestr(re_filename, _repdf_bytes)

                            print('######################## After create_label for re_package ######################## ', re_filename,)
                        # break
                        # else:
                        #     continue

                    else:
                        # self.message_user(request, f"⚠️ Błąd tworzenia przesyłki allegro dla zamówienia {order.order_id} u sprzedawcy {vendor.name}: {resp.status_code} - {resp.text}", level='error')
                        order.error = f"❌ 1765 {resp.status_code} - {resp.json().get('errors', [{}])[0].get('userMessage')}\n"
                        order.save(update_fields=['error'])
                        # print('######################## Error creating shipment ######################## ', resp.status_code, resp.text )
                        continue

            # print('######################## Final package to be sent ######################## ', packages)

            resp = create_shipment(ALLEGRO_API_URL, order.vendor, order, packages)
            print('Creating shipment resp ----------------', resp, resp.text)
            if resp.status_code == 200 or resp.status_code == 201:
                filename, pdf_bytes = create_label(order, ALLEGRO_API_URL, resp, order.vendor, headers, errors, zip_file)
                # print('######################## After create_label ######################## ', filename, pdf_bytes)
                if filename and pdf_bytes: 
                    zip_file.writestr(filename, pdf_bytes)
                    print('######################## Written to zip ######################## ', filename,)
                # break
    
            else:
                print('######################## Error creating shipment ######################## ', resp.status_code, resp.text )
                # self.message_user(request, f"⚠️ Błąd tworzenia przesyłki allegro dla zamówienia {order.order_id} u sprzedawcy {vendor.name}: {resp.status_code} - {resp.text}", level='error')
                order.error = f"❌ 1765 {resp.status_code} - {resp.json().get('errors', [{}])[0].get('userMessage')}\n"
                order.save(update_fields=['error'])
                continue
                    
            # elif response.status_code == 401:
            #     self.message_user(request, f"⚠️ Nieprawidłowy token dostępu dla {vendor.name}", level='error')
            #     continue

        # if errors:
        self.message_user(request, f"⚠️ Błędy podczas tworzenia przesyłki allegro dla zamówienia {order.order_id} u sprzedawcy {order.vendor.name}:\n{order.error}", level='error')
                    
        zip_file.close() 
        # Prepare ZIP for download 
        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip") 
        response["Content-Disposition"] = 'attachment; filename="labels.zip"'
        print("________________RETURN IS HERE______________________")
 
        return response
    
    create_allegro_orders.short_description = "📦 Utwórz przesyłki allegro"




    def dbg(self, label, value):
        """Pretty‑print any value safely, even if it's None or deeply nested."""
        import json

        try:
            pretty = json.dumps(value, indent=4, ensure_ascii=False)
        except Exception:
            pretty = str(value)

        print(f"\n===== DEBUG: {label} =====")
        print(pretty)
        print("====================================\n")


    def fetch_and_store_allegro_orders(self, request, queryset=None):
        vendors = Vendor.objects.filter(marketplace='allegro.pl')

        for vendor in vendors:

            last_order = AllegroOrder.objects.filter(vendor=vendor).order_by('-id').first()
            if last_order:
                url = f"https://{ALLEGRO_API_URL}/order/events?from={last_order.event_id}" # &type=READY_FOR_PROCESSING
            else:
                url = f"https://{ALLEGRO_API_URL}/order/events" # ?type=READY_FOR_PROCESSING
            try:
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

                # for event in events:
                #     # print('Processing event ----------------', event)
                #     order = event.get('order') or {}
                #     checkout_form = order.get('checkoutForm') or {}
                #     checkout_form_id = checkout_form.get('id', '')
                #     if not checkout_form_id:
                #         continue

                #     buyer_info = self.get_buyer_info(checkout_form_id, vendor.access_token, vendor.name) or {}
                #     buyer = buyer_info.get('buyer') or {}
                #     invoice = buyer_info.get('invoice') or {}
                #     address = invoice.get('address') or {}
                #     company = address.get('company') or {}
                #     if company:
                #         ids = company.get('ids') or []
                #         buyer_nip = ids[0].get('value') if ids else 'brak'
                #     else:
                #         buyer_nip = 'brak'

                #     line_items = order.get('lineItems') or []

                #     delivery = buyer_info.get('delivery') or {}
                #     delivery_method_id = delivery.get('method', {}).get('id')
                #     delivery_method_name = delivery.get('method', {}).get('name')
                #     pickup_point_id = delivery.get('pickupPoint', {}).get('id')
                #     pickup_point_name = delivery.get('pickupPoint', {}).get('name')
                #     delivery_cost = float(delivery.get('cost', {}).get('amount', 0))
                #     is_smart = delivery.get('smart', 'brak')

                #     # print(' ######### ######### ######### buyer_info delivery ----------------', delivery)
                #     # print(' ######### ######### ######### buyer_info delivery_cost ----------------', delivery_cost)
                #     # print(' ######### ######### ######### buyer_info is_smart ----------------', is_smart)


                #     # print('company ----------------', company.get('name', ''))
                #     # print('buyer_zipcode ----------------', buyer.get('address', {}).get('postCode', ''))

                #     # delivery_cost = float(buyer_info['delivery']['cost']['amount']) or 0.00
                #     is_smart = buyer_info.get('delivery', {}).get('smart', 'brak')

                #     # --- 1. Utwórz/aktualizuj nagłówek zamówienia ---
                #     allegro_order, created = AllegroOrder.objects.update_or_create(
                #         event_id=event['id'],
                #         order_id=checkout_form_id,
                #         vendor=vendor,
                #         delivery_method_id=delivery_method_id,
                #         delivery_method_name=delivery_method_name,
                #         pickup_point_id=pickup_point_id,
                #         pickup_point_name=pickup_point_name,
                #         defaults={
                #             'buyer_login': buyer.get('login', ''),
                #             'buyer_email': buyer.get('email', ''),
                #             'buyer_name': f'{buyer.get("firstName", "")} {buyer.get("lastName", "")}',
                #             'buyer_company_name': buyer.get("companyName", ""),
                #             'buyer_street': buyer.get('address', {}).get('street', ''),
                #             'buyer_zipcode': buyer.get('address', {}).get('postCode', ''),
                #             'buyer_city': buyer.get('address', {}).get('city', ''),
                #             'buyer_nip': buyer_nip,
                #             'occurred_at': parse_datetime(event['occurredAt']),
                #             'type': event['type'],
                #             'is_smart': is_smart,
                #             'delivery_cost': delivery_cost #0 if is_smart else delivery_cost,
                #         }
                #     )

                for event in events:

                    print('Processing event ######### ######### ######### ', event)

                    # self.dbg("EVENT RAW", event)

                    order = event.get('order') or {}
                    # self.dbg("ORDER", order)

                    checkout_form = order.get('checkoutForm') or {}
                    checkout_form_id = checkout_form.get('id', '')
                    # self.dbg("CHECKOUT FORM", checkout_form)

                    if not checkout_form_id:
                        continue

                    buyer_info = self.get_buyer_info(checkout_form_id, vendor.access_token, vendor.name) or {}
                    self.dbg("BUYER INFO", buyer_info)

                    buyer = buyer_info.get('buyer') or {}
                    # self.dbg("BUYER", buyer)

                    delivery_address = buyer_info.get('delivery', {}).get('address', '') #buyer_info.get('delivery')
                    self.dbg("delivery_address", delivery_address)

                    invoice = buyer_info.get('invoice') or {}
                    address = invoice.get('address') or {}
                    company = address.get('company') or {}
                    # self.dbg("INVOICE", invoice)
                    # self.dbg("ADDRESS", address)
                    # self.dbg("COMPANY", company)

                    if company:
                        ids = company.get('ids') or []
                        buyer_nip = ids[0].get('value') if ids else 'brak'
                    else:
                        buyer_nip = 'brak'
                    # self.dbg("BUYER NIP", buyer_nip)

                    line_items = order.get('lineItems') or []
                    # self.dbg("LINE ITEMS", line_items)

                    delivery = buyer_info.get('delivery') or {}
                    # self.dbg("DELIVERY", delivery)

                    delivery_method = delivery.get('method') or {}
                    pickup_point = delivery.get('pickupPoint') or {}
                    cost = delivery.get('cost') or {}

                    delivery_method_id = delivery_method.get('id')
                    delivery_method_name = delivery_method.get('name')
                    pickup_point_id = pickup_point.get('id')
                    pickup_point_name = pickup_point.get('name')
                    delivery_cost = float(cost.get('amount', 0))
                    is_smart = delivery.get('smart', 'brak')

                    # self.dbg("DELIVERY METHOD", delivery_method)
                    # self.dbg("PICKUP POINT", pickup_point)
                    # self.dbg("DELIVERY COST", delivery_cost)
                    # self.dbg("IS SMART", is_smart)

                    allegro_order, created = AllegroOrder.objects.update_or_create(
                        event_id=event['id'],
                        order_id=checkout_form_id,
                        vendor=vendor,
                        delivery_method_id=delivery_method_id,
                        delivery_method_name=delivery_method_name,
                        pickup_point_id=pickup_point_id,
                        pickup_point_name=pickup_point_name,
                        delivery_address=delivery_address,
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
                            'delivery_cost': delivery_cost,
                        }
                    )

                    # self.dbg("ORDER SAVED", {
                    #     "id": allegro_order.id,
                    #     "created": created,
                    #     "order_id": allegro_order.order_id,
                    # })


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
                    if event['type'] == 'READY_FOR_PROCESSING':
                        invoice_required = invoice.get('required', False)
                        invoice_data = {
                            'created_at': now(),
                            'buyer_email': allegro_order.buyer_email,
                            'vendor': allegro_order.vendor,
                            'is_generated': True,
                        }

                        if invoice_required:
                            invoice_data.update({
                                'buyer_name': invoice.get('address', {}).get('company', {}).get('name', allegro_order.buyer_login),
                                'buyer_street': invoice.get('address', {}).get('street', ''),
                                'buyer_zipcode': invoice.get('address', {}).get('zipCode', ''),
                                'buyer_city': invoice.get('address', {}).get('city', ''),
                                'buyer_nip': invoice.get('address', {}).get('company', {}).get('ids', [{}])[0].get('value', 'brak'),
                            })
                        else:
                            invoice_data.update({
                                'buyer_name': f"{buyer.get('firstName', '')} {buyer.get('lastName', '')}", # allegro_order.buyer_login,
                                'buyer_street': buyer.get('address', {}).get('street', ''),
                                'buyer_zipcode': buyer.get('address', {}).get('postalCode', ''),
                                'buyer_city': buyer.get('address', {}).get('city', ''),
                                'buyer_nip': 'Brak',
                            })

                        Invoice.objects.update_or_create(
                            allegro_order=allegro_order,
                            defaults=invoice_data
                        )

                        allegro_order.invoice_generated = True
                        allegro_order.save(update_fields=['invoice_generated'])

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


    @admin.action(description="🧾 Wiadomość do klienta")
    def send_auto_message(self, request, queryset):

        message = Message.objects.get(title='Wiadomość po opłaceniu')
        url = f"https://{ALLEGRO_API_URL}/messaging/messages"
        
        for q in queryset:

            headers = {
                "Authorization": f"Bearer {q.vendor.access_token}",
                "Accept": "application/vnd.allegro.public.v1+json",
                "Content-Type": "application/vnd.allegro.public.v1+json"
            }

            payload = {
                "recipient": {
                    "login": f"{q.buyer_login}"
                },
                "order": {
                    "id": f"{q.order_id}"
                    },
                "text": f"{message.text}",
                "attachments": []
            }

            try:
                response = allegro_request("POST", url, q.vendor.name, headers=headers, data=json.dumps(payload))

                if response.status_code == 201:
                    self.message_user(
                        request,
                        f"✅ Wiadomość została wysłana",
                        level="success"
                    )
                    q.message_sent = True
                    q.save(update_fields=['message_sent'])
                else:
                    # parse Allegro error response
                    errors = response.json().get("errors", [])
                    for err in errors:
                        self.message_user(
                            request,
                            f"⚠️ Błąd wysłania wiadomości: {err}",
                            level="error"
                        )

                time.sleep(1) 

            except requests.exceptions.HTTPError as err:
                errors = response.json().get("errors", [])
                for err in errors:
                    self.message_user(
                        request,
                        f"⚠️ Błąd wysłania wiadomości: {err}",
                        level="error"
                    )
                raise SystemExit(err)


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
            'fields': ('vendor', 'order_items_display', 'shop_order_items_display', 'delivery_cost_display', 'order_date')
        }),
    )

    readonly_fields = (
        'created_at', 'formatted_generated', 'corrected', #'invoice_number', 
        'order_items_display', 'shop_order_items_display', 'delivery_cost_display', 'order_date', #'allegro_order', shop_order
    )

    # readonly_fields = ('created_at',)

    list_display = ['invoice_number', 'is_generated', 'sent_to_buyer', 'buyer_name', 'vendor', 'created_at']
    search_fields = ['invoice_number', 'buyer_name', 'buyer_email', 'shop_order__oid',]
    autocomplete_fields = ('allegro_order', 'shop_order')
    # list_editable = ['allegro_order', 'shop_order']
    list_filter = ['is_generated', 'sent_to_buyer', 'vendor', 'created_at']
    actions = ['print_invoice_pdf', 'generate_invoice', 'create_correction']
    inlines = [InvoiceCorrectionInline]


    def formatted_generated(self, obj):
        return localtime(obj.generated_at).strftime('%d-%m-%Y') if obj.generated_at else "—"
    formatted_generated.short_description = "Data wygenerowania"



    def shop_order_items_display(self, obj):
        # Pobierz pozycje z shop_order
        items = None
        if getattr(obj, "shop_order", None):
            items = obj.shop_order.orderitem.all()
            print('shop_order_items_display items -----------', items)

        # Jeśli brak → zwróć komunikat
        if not items or not items.exists():
            return "Brak pozycji"

        # Renderuj tabelę
        rows = format_html_join(
            '\n',
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
            (
                (
                    getattr(item, "product", getattr(item.product, "title", "")),
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

    shop_order_items_display.short_description = "Produkty w zamówieniu (Shop):"



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
                    # print(f'{vendor.marketplace}-------------------')
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
                    resp = post_invoice_to_allegro(vendor, invoice, pdf_content, False)
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


@admin.register(InvoiceCorrection)
class InvoiceCorrectionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Faktura', {
            'fields': ('invoice_number', 'created_at', 'sent_to_buyer', 'allegro_order') #'allegro_order', 
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
                resp = post_invoice_to_allegro(vendor, invoice, pdf_content, True)

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
    list_display = ['oid', 'order_items_display', 'payment_status', 'order_status', 'delivery', 'shipping_label', 'delivery_status', 'sub_total', 'shipping_amount', 'total', 'date']
    actions = ['generate_pdf_labels', 'generate_invoice_webstore', 'print_invoice_pdf_webstore']

    inlines = [CartOrderItemsInlineAdmin, InvoiceInline, InvoiceCorrectionInline, InvoiceFileInline]


    def order_items_display(self, obj):
        items = obj.orderitem.all()
        if not items:
            return "Brak pozycji"
        
        rows = format_html_join(
            '\n',
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
            (
                (
                    item.product.title,
                    f"{item.price:.2f} PLN",
                    item.qty,
                    f"{(item.price * item.qty):.2f} PLN"
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
admin.site.register(Message)
admin.site.register(Address)
admin.site.register(AllegroBatch)
admin.site.register(AllegroProductBatch)
admin.site.register(AllegroProductUpdateLog)
admin.site.register(SeoTitleBatch)
admin.site.register(SeoTitleLog)
