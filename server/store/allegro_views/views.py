import asyncio
from decimal import Decimal
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import redirect, render
from django import forms

import requests
import json
import os
from dotenv import load_dotenv

import aiohttp
import asyncio

# from store.models import Invoice
from vendor.models import Vendor


# Load variables from .env into environment
load_dotenv()

# Access them like normal environment variables
ALLEGRO_API_URL = os.getenv("ALLEGRO_API_URL")
ALL_GRO_API_URL = os.getenv("ALL_GRO_API_URL")
AUTH_URL = os.getenv("AUTH_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")
_marketplace = os.environ.get("marketplace")


def get_access_token(authorization_code, vendor_name):
    print("Getting access token...----------------", authorization_code, vendor_name)
    vendor = Vendor.objects.get(name=vendor_name)
    print("Getting RETSET_CLIENT_ID...----------------", vendor.client_id)
    print("Getting access RETSET_CLIENT_SECRET...----------------", vendor.secret_id)

    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': f"{REDIRECT_URI}/allegro-auth-code/{vendor_name}"}
        response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(vendor.client_id, vendor.secret_id))

        # print("RESPONSE CONTENT *$*$*$*$*$*$*$*$*$*$*$:", response.text)
        
        # print("Status --------------------------- :", response.status_code)
        # print("Body --------------------------- :", response.text)

        response.raise_for_status()  # This will raise HTTPError if status is 4xx/5xx

        tokens = response.json()
        # return tokens['access_token']
        return tokens
    except requests.exceptions.RequestException as err:
        print("Request failed:", err)
        raise

    

@api_view(['POST'])
def exchange_token_view(request, code, vendor_name):
    # print("Getting exchange_token_view...----------------", code, vendor_name)
    authorization_code = code #request.data.get('code')
    if not authorization_code:
        return JsonResponse({'error': 'Missing authorization code'}, status=400)

    try:
        tokens = get_access_token(authorization_code, vendor_name)
        if tokens:
            # print("Response get_access_token ---------------:", tokens)
            vendor = Vendor.objects.get(name=vendor_name)
            vendor.access_token = tokens['access_token']
            vendor.refresh_token = tokens['refresh_token']
            vendor.save()
        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

def get_next_token(token, vendor_name):

    vendor = Vendor.objects.get(name=vendor_name)
    try:
        data = {'grant_type': 'refresh_token', 'refresh_token': token, 'redirect_uri': f"{REDIRECT_URI}/allegro-auth-code/{vendor_name}"}
        get_next_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(vendor.client_id, vendor.secret_id))
        print("Response get_next_token_response ---------------:", get_next_token_response)
        tokens = json.loads(get_next_token_response.text)
        vendor.access_token = tokens['access_token']
        vendor.refresh_token = tokens['refresh_token']
        vendor.save(update_fields=['access_token', 'refresh_token'])
        return tokens['access_token']
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

# import requests
# from django.conf import settings

async def async_allegro_request(method, url, vendor, **kwargs):
    print("allegro_request CALLED:-----------------------")
    """
    Wrapper for Allegro API requests that auto-refreshes token on 401.
    """

    # Ensure Authorization header
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {vendor.access_token}"
    kwargs["headers"] = headers

    response = requests.request(method, url, **kwargs)
    # print(f' TRACE ID #########', response.headers.get("Trace-Id"))
    # print(f' VENDOR NAME ######### {vendor_name}')
    # print(f' URL ######### {url}')
    # print(f' METHOD ######### {method}')
    # print(f' RESPONSE ######### {response}')
    # print(f' RESPONSE TEXT ######### {response.text}')

    if response.status_code == 401:
        # Refresh token
        new_token = get_next_token(vendor.refresh_token, vendor.name)

        # Retry with new token
        headers["Authorization"] = f"Bearer {new_token}"
        kwargs["headers"] = headers
        response = requests.request(method, url,**kwargs)

    return response

def allegro_request(method, url, vendor_name, **kwargs):
    # print("allegro_request CALLED:-----------------------")
    """
    Wrapper for Allegro API requests that auto-refreshes token on 401.
    """

    vendor = Vendor.objects.get(name=vendor_name)

    # Ensure Authorization header
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {vendor.access_token}"
    kwargs["headers"] = headers

    response = requests.request(method, url, **kwargs)
    # print(f' TRACE ID #########', response.headers.get("Trace-Id"))
    # print(f' VENDOR NAME ######### {vendor_name}')
    # print(f' URL ######### {url}')
    # print(f' METHOD ######### {method}')
    # print(f' RESPONSE ######### {response}')
    # print(f' RESPONSE TEXT ######### {response.text}')

    if response.status_code == 401:
        # Refresh token
        new_token = get_next_token(vendor.refresh_token, vendor_name)

        # Retry with new token
        headers["Authorization"] = f"Bearer {new_token}"
        kwargs["headers"] = headers
        response = requests.request(method, url, **kwargs)

    elif response.status_code == 403:
        # Refresh token
        new_token = get_next_token(vendor.refresh_token, vendor_name)

        # Retry with new token
        headers["Authorization"] = f"Bearer {new_token}"
        kwargs["headers"] = headers
        response = requests.request(method, url, **kwargs)

        print(f' RESPONSE 403 retry ######### {response}')
        print(f' RESPONSE TEXT 403 retry ######### {response.text}')

    return response


def parse_allegro_response(resp, action):
    data = resp.json()

    print(f'parse_allegro_response ACTION ######### {action}')
    print(f'parse_allegro_response RESPONSE ######### {resp}')
    print(f'parse_allegro_response RESPONSE TEXT ######### {resp.text}')
    print(f'parse_allegro_response DATA ######### {data}')

    # jeśli Allegro zwróciło błąd
    if "errors" in data and data["errors"]:
        err = data["errors"][0]
        return {
            "success": False,
            "message": err.get("userMessage") or err.get("message") or "Nieznany błąd"
        }

    # jeśli wszystko OK
    return {
        "success": True,
        "message": f"Zaktualizowano: {action}"
    }


# def fetch_all_offers(vendor_name, headers):

#         statuses = ["ACTIVE", "INACTIVE", "ENDED", "ACTIVATING", "NOT_LISTED"]
#         all_offers = []

#         for status in statuses:
#             offset = 0
#             while True:
#                 url = (
#                     f"https://{ALLEGRO_API_URL}/sale/offers"
#                     f"?limit=100&offset={offset}"
#                     f"&publication.marketplace=allegro-pl"
#                     f"&publication.status={status}"
#                 )
#                 response = allegro_request("GET", url, vendor_name, headers=headers)
#                 data = response.json()

#                 offers = data.get("offers", [])
#                 if not offers:
#                     break

#                 all_offers.extend(offers)
#                 offset += 100

#                 total_count = data.get("totalCount")
#                 if total_count and offset >= total_count:
#                     break
               
#         for offer in all_offers:
#             print(f' ################### "offer id & status" ################### ', offer.get("id"), offer.get("publication", {}).get("status"))

#         return all_offers



# def create_product_from_allegro(offer, vendor):

#     sku = offer.get("external", {}).get("id")
#     if not sku:
#         return None

#     price_brutto = Decimal(str(offer["sellingMode"]["price"]["amount"]))
#     price_netto = (price_brutto / Decimal("1.23")).quantize(Decimal("0.01"))

#     product = Product.objects.create(
#         sku=sku,
#         title=offer.get("name", "Produkt Allegro"),
#         price_brutto=price_brutto,
#         price=price_netto,
#         stock_qty=offer.get("stock", {}).get("available", 0),
#         allegro_status=offer.get("publication", {}).get("status"),
#         allegro_in_stock=offer.get("publication", {}).get("status") == "ACTIVE",
#         allegro_started_at=offer.get("publication", {}).get("startedAt"),
#         allegro_ended_at=offer.get("publication", {}).get("endedAt"),
#         allegro_watchers=offer.get("stats", {}).get("watchersCount", 0),
#         allegro_visits=offer.get("stats", {}).get("visitsCount", 0),
#     )

#     # --- zachowaj vendorów z mojastrona.pl ---
#     local_vendors = product.vendors.filter(marketplace="mojastrona.pl")

#     # --- ustaw aktualnego vendora Allegro + lokalnych vendorów ---
#     product.vendors.set([vendor, *local_vendors])

#     # kategoria
#     cat_id = offer.get("category", {}).get("id")
#     if cat_id:
#         try:
#             category = Category.objects.get(allegro_cat_id=cat_id)
#             product.category = category
#         except Category.DoesNotExist:
#             pass

#     # zdjęcia
#     img = offer.get("primaryImage", {}).get("url")
#     if img:
#         product.img_links = [img]

#     product.save()
#     return product



import random
import string

def generate_pid(length=10):
    alphabet = "abcdefghijklmnopqrstuvxyz"
    return ''.join(random.choice(alphabet) for _ in range(length))


# def clone_product_with_new_allegro_id(product, new_allegro_id, vendor):
#     # skopiuj bazowy produkt
#     original_pk = product.pk
#     original_vendors = list(product.vendors.all())

#     product.pk = None  # nowy rekord
#     product.allegro_id = new_allegro_id

#     # nowy pid i unikalny slug
#     product.pid = generate_pid()
#     if product.slug:
#         product.slug = f"{product.slug}-{new_allegro_id}"

#     # wyczyść pola allegro (zaraz i tak nadpiszesz syncem)
#     product.allegro_status = None
#     product.allegro_in_stock = False
#     product.allegro_watchers = 0
#     product.allegro_visits = 0
#     product.allegro_started_at = None
#     product.allegro_ended_at = None

#     product.save()

#     # --- zachowaj vendorów z mojastrona.pl ---
#     local_vendors = product.vendors.filter(marketplace=_marketplace)

#     # --- ustaw aktualnego vendora Allegro + lokalnych vendorów ---
#     product.vendors.set([vendor, *local_vendors])

#     return product


def get_allegro_id(vendor_name, allegro_ids):
    for entry in allegro_ids:
        if entry["vendor"] == vendor_name:
            return entry["product_id"]
    return None

def save_allegro_id(vendor_name, allegro_ids, new_id):
    for entry in allegro_ids:
        if entry["vendor"] == vendor_name:
            entry["product_id"] = new_id
            return allegro_ids
    allegro_ids.append({"vendor": vendor_name, "product_id": new_id})
    return allegro_ids




    # needed functions??

@method_decorator(staff_member_required, name='dispatch')
class AllegroOrderAdminView(View):
    def get(self, request):
        from store.admin import AllegroOrderAdmin
        from store.models import AllegroOrder

        admin_instance = AllegroOrderAdmin(AllegroOrder, admin_site=None)
        admin_instance.fetch_and_store_allegro_orders(request, queryset=None)

        messages.success(request, "✅ Synchronizacja Allegro zakończona.")
        return redirect('/admin/store/allegroorder/')
    

# class AllegroCreateOrderView(View):
#     def get(self, request):
#         from store.admin import AllegroOrderAdmin
#         from store.models import AllegroOrder

#         admin_instance = AllegroOrderAdmin(AllegroOrder, admin_site=None)
#         admin_instance.create_allegro_orders(request, queryset)

#         messages.success(request, "✅ Tworzenie zamówień Allegro zakończone.")
#         return redirect('/admin/store/allegroorder/')
    

@method_decorator(staff_member_required, name='dispatch')
class ProductAdminView(View):
    def get(self, request):
        from store.admin import ProductAdmin
        from store.models import Product

        admin_instance = ProductAdmin(Product, admin_site=None)

        batch_id = admin_instance.sync_allegro_offers(request, queryset=None)

        messages.success(request, "🔄 Synchronizacja Allegro została uruchomiona w tle.")

        return redirect(f"/api/store/admin/allegroupdatebatch/{batch_id}/status/")

    
# @method_decorator(staff_member_required, name='dispatch')
# class EditProductAdminView(View):
#     def get(self, request):
#         from store.admin import ProductAdmin
#         from store.models import Product

#         print("EditProductAdminView POST request received.****************")

#         # pobierz listę ID z POST (np. zaznaczone w adminie)
#         # ids = request.POST.getlist("ids")  # np. ['1','2','3']
#         # queryset = Product.objects.filter(pk__in=ids)

#         admin_instance = ProductAdmin(Product, admin_site=None)
#         admin_instance.update_products_description(request, queryset=None)

#         messages.success(request, "✅ Edytowanie ofert Allegro zakończone.")
#         return redirect('/admin/store/product/')


# @method_decorator(staff_member_required, name='dispatch')
# class EditProductAdminView(View):
#     async def get(self, request):
#         from store.admin import ProductAdmin
#         from store.models import Product

#         print("EditProductAdminView GET request received.****************")

#         admin_instance = ProductAdmin(Product, admin_site=None)
#         # zwykła metoda – nie jest async, więc wywołujesz normalnie
#         admin_instance.update_products_description(request, queryset=None)

#         messages.success(request, "✅ Edytowanie ofert Allegro zakończone.")
#         return redirect('/admin/store/product/')


@method_decorator(staff_member_required, name='dispatch')
class EditProductAdminView(View):
    def get(self, request):
        from store.admin import ProductAdmin
        from store.models import Product, Vendor

        print("EditProductAdminView GET request received.****************")

        # ✅ Do all ORM queries here (sync context)
        vendors = list(Vendor.objects.filter(marketplace='allegro.pl'))
        products = list(Product.objects.filter(allegro_in_stock=True).prefetch_related("vendors"))

        tasks_data = []
        for vendor in vendors:
            access_token = vendor.access_token
            producer = responsible_producers(vendor)

            for product in products:
                if vendor in product.vendors.all():   # ORM call is safe here
                    url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{product.allegro_id}"
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

        # ✅ Now run async HTTP tasks only (no ORM inside async)
        results = asyncio.run(_run_patch_tasks(vendor, tasks_data))
        print("All PATCH results:", results)

        messages.success(request, "✅ Edytowanie ofert Allegro zakończone.")
        return redirect('/admin/store/product/')


async def responsible_producers(vendor):
    print("responsible_producers CALLED:-----------------------")
    url = f"https://{ALLEGRO_API_URL}/sale/responsible-producers"
    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {vendor.access_token}'
    }
    response = await async_allegro_request("GET", url, vendor, headers=headers)
    return response.json()


async def _run_patch_tasks(vendor, tasks_data):
    print("_run_patch_tasks CALLED:-----------------------")
    # tasks = []
    # async with aiohttp.ClientSession() as session:
    #     for data in tasks_data:
    #         tasks.append(asyncio.create_task(_patch_offer(vendor, session, data))) #asyncio.create_task(get_shipment_id(request, secret, name, deliveryMethod))
    #     return await asyncio.gather(*tasks, return_exceptions=True)
    async with aiohttp.ClientSession() as session:
        tasks = [
            _patch_offer(vendor, session, data)
            for data in tasks_data
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


async def _patch_offer(vendor, session, data):
    print("_patch_offer CALLED:-------------------")
    safe_html = await sanitize_allegro_description(data["description"])
    payload = json.dumps({
        "name": data["title"],
        "external": {"id": data["sku"]},
        "productSet": [{"product": {"id": data["ean"], "idType": "GTIN"}}],
        "sellingMode": {"price": {"amount": str(data["price"]), "currency": "PLN"}},
        "stock": {"available": data["stock_qty"]},
        "description": {"sections": [{"items": [{"type": "TEXT", "content": safe_html}]}]},
        "images": await build_images(vendor, data["img_links"], data["vendor_name"])
    })
    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {data["access_token"]}'
    }

    async with session.patch(data["url"], headers=headers, data=payload) as response:
        text = await response.text()
        print(f'PATCH {data["sku"]} RESPONSE STATUS###############: {response.status}, BODY#############: {text}')
        return response.status
    
from bs4 import BeautifulSoup
async def sanitize_allegro_description(html: str) -> str:
        print("sanitize_allegro_description CALLED:-----------------------")
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


async def upload_image(url, vendor):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://{ALLEGRO_API_URL}/sale/images",
            headers={
                "Accept": "application/vnd.allegro.public.v1+json",
                "Content-Type": "application/vnd.allegro.public.v1+json",
                "Authorization": f"Bearer {vendor.access_token}",  # ✅ token dostępu
            },
            json={"url": url}
        ) as response:
            data = await response.json()
            if "location" not in data:
                # log the error response for debugging
                print("Upload image failed:", data)
                return None
            return data["location"]



async def build_images(vendor, img_links, vendor_name):
    tasks = [upload_image(link, vendor) for link in img_links]
    uploaded = await asyncio.gather(*tasks, return_exceptions=True)
    # keep only successful string URLs
    return [{"url": u} for u in uploaded if isinstance(u, str)]




# def correction_view(self, request, invoice_id):
#         invoice = Invoice.objects.get(pk=invoice_id)
#         products = invoice.products  # zakładam, że masz JSONField albo relację na produkty

#         # dynamiczny formularz
#         class DynamicCorrectionForm(forms.Form):
#             def __init__(self, *args, **kwargs):
#                 super().__init__(*args, **kwargs)
#                 for i, product in enumerate(products, start=1):
#                     self.fields[f"quantity_{i}"] = forms.IntegerField(
#                         label=f"{product['offer']['name']}",
#                         initial=product['quantity'],
#                         min_value=0
#                     )

#         if request.method == "POST":
#             form = DynamicCorrectionForm(request.POST)
#             if form.is_valid():
#                 corrected_products = []
#                 for i, product in enumerate(products, start=1):
#                     new_qty = form.cleaned_data[f"quantity_{i}"]
#                     corrected_products.append({
#                         **product,
#                         "quantity": new_qty
#                     })

#                 # utwórz nową fakturę korekcyjną
#                 correction = Invoice.objects.create(
#                     invoice_number=f"KOREKTA-{invoice.invoice_number}",
#                     shop_order=invoice.shop_order,
#                     allegro_order=invoice.allegro_order,
#                 )
#                 # zakładam, że masz pole JSONField na produkty
#                 correction.products = corrected_products
#                 correction.save()

#                 self.message_user(request, f"Utworzono korektę faktury nr {invoice.invoice_number}")
#                 return redirect("..")  # powrót do listy faktur
#         else:
#             form = DynamicCorrectionForm()

#         context = {
#             "form": form,
#             "invoice": invoice,
#             "title": f"Korekta faktury nr {invoice.invoice_number}",
#         }
#         return render(request, "admin/invoice_correction.html", context)