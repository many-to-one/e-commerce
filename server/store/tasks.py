import json
import requests
import io, os
import zipfile
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from celery import shared_task, group, chord
from django.db import transaction

from django.utils import timezone
from datetime import timedelta

from .allegro_views.product_views import action_with_offer_from_product

from .allegro_views.create_label import create_label
from .allegro_views.create_shipment import create_shipment
from .allegro_views.views import allegro_request, parse_allegro_response, responsible_producers
from users.models import User
from .models import (
    AllegroProductBatch,
    AllegroProductUpdateLog, 
    ClientAccessLog, 
    Product, Gallery, 
    DeliveryCouriers, AllegroOrder, 
    Vendor, AllegroBatch, Product, 
    SeoTitleLog, SeoTitleBatch,
    )
from .services.openai_client import generate_allegro_seo_title

from django.conf import settings



# Access them like normal environment variables
ALLEGRO_API_URL = os.getenv("ALLEGRO_API_URL")
PAYU_API_URL = os.getenv("PAYU_API_URL")
_marketplace = os.getenv("marketplace")



def compress_image(image: Image.Image, max_size_kb=200):
    """
    Compress image while keeping aspect ratio.
    - Reduces quality if needed to fit within `max_size_kb`.
    """
    output = BytesIO()
    quality = 85  # Start with high quality
    image.save(output, format="JPEG", quality=quality, optimize=True)
    
    while output.tell() > max_size_kb * 1024 and quality > 10:
        output.seek(0)
        quality -= 5
        output.truncate()
        image.save(output, format="JPEG", quality=quality, optimize=True)
    
    output.seek(0)
    return output

@shared_task
def store_product_images(product_id, img_links): 
    print('############ CELEY ##########', product_id, img_links)
    # try:
    #     product = Product.objects.get(id=product_id)
    #     # img_links = product.img_links

    #     if not img_links:
    #         return f"No images found for product {product_id}"

    #     for index, img_url in enumerate(img_links):
    #         response = requests.get(img_url.strip(), timeout=10)
    #         if response.status_code == 200:
    #             img = Image.open(BytesIO(response.content))
    #             img = img.convert("RGB")  # Convert to RGB to avoid format issues
                
    #             # Compress image
    #             compressed_img = compress_image(img)

    #             # Save first image as `product.image`
    #             if index == 0:
    #                 product.image.save(f"product_{product.id}.jpg", ContentFile(compressed_img.read()), save=True)
    #             else:
    #                 # Save the rest as gallery images
    #                 gallery_img = Gallery(product=product)
    #                 gallery_img.image.save(f"gallery_{product.id}_{index}.jpg", ContentFile(compressed_img.read()), save=True)

    #     return f"Images for product {product_id} stored successfully"

    # except Product.DoesNotExist:
    #     return f"Product {product_id} does not exist"
    # except Exception as e:
    #     return f"Error: {str(e)}"

from django.utils.timezone import now
from datetime import timedelta

@shared_task
def enrich_and_log_client_info(data):
    ip = data['ip']
    user_agent = data['user_agent'].lower()
    username = data.get('username')
    if username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
    else:
        user = None
    # print('Celery user++++++++++++++++++++', user)

    # Geo lookup
    geo_location = get_geo_from_ip(ip)

    # Device type
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        device_type = 'Mobile'
    elif 'ipad' in user_agent or 'tablet' in user_agent:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'

    # OS detection
    os = 'Unknown'
    if 'windows' in user_agent:
        os = 'Windows'
    elif 'mac os' in user_agent or 'macintosh' in user_agent:
        os = 'macOS'
    elif 'linux' in user_agent:
        os = 'Linux'
    elif 'android' in user_agent:
        os = 'Android'
    elif 'iphone' in user_agent or 'ios' in user_agent:
        os = 'iOS'

    recent = ClientAccessLog.objects.filter(
        ip_address=ip,
        device_type=device_type,
        accessed_at__gte=now() - timedelta(hours=1)
    )


    if recent.exists():
        return

    # Final log
    ClientAccessLog.objects.create(
        user=user,
        ip_address=ip,
        device_type=device_type,
        operating_system=os,
        user_agent=data['user_agent'],
        geo_location=geo_location,
        language=data['language'],
        referer=data['referer'],
        cookies=data['cookies'],
    )

def get_geo_from_ip(ip):
    try:
        res = requests.get(f'https://ipinfo.io/{ip}/json', timeout=2)
        data = res.json()
        # print('############################ get_geo_from_ip ############################', data)
        # Clean up empty or malformed fields
        location = {
            'ip': data.get('ip', ''),
            'city': data.get('city', ''),
            'region': data.get('region', ''),
            'country': data.get('country', ''),
            'loc': data.get('loc', ''),  # lat,long
            'org': data.get('org', ''),
        }
        # Remove empty strings
        return {k: v for k, v in location.items() if v}
    except Exception as e:
        print(f'Geo lookup failed for IP {ip}: {e}')
        return {}

@shared_task
def test(x, y):
    # print('Test celery task running.../////////////////////////////////', x + y)
    return x + y


########## REMOVE BACKGROUND LOGIC ##########

# @shared_task
# def generate_thumbnail(product_id, image_url, width=200, height=200):
#     print('generate_thumbnail celery task running.../////////////////////////////////', product_id)
#     from rembg import remove
#     try:
#         # Download image
#         response = requests.get(image_url, timeout=10)
#         response.raise_for_status()

#         # Remove background using rembg (returns bytes with alpha channel)
#         input_bytes = response.content
#         output_bytes = remove(input_bytes)  # PNG with transparency

#         # Open with Pillow
#         pil_img = Image.open(BytesIO(output_bytes)).convert("RGBA")

#         # Resize thumbnail
#         pil_img.thumbnail((width, height), Image.LANCZOS)

#         # Save to buffer (WebP supports alpha channel)
#         buffer = BytesIO()
#         pil_img.save(buffer, format="WEBP", quality=80)
#         buffer.seek(0)

#         # Attach to product
#         product = Product.objects.get(id=product_id)
#         product.thumbnail.save(
#             f"{product.sku}_thumb.webp",
#             ContentFile(buffer.read()),
#             save=True
#         )

#     except Exception as e:
#         print(f"Thumbnail generation failed: {e}")


@shared_task
def generate_thumbnail(product_id, image_url, width=200, height=200):
    # print('Generating thumbnail for////////////////////////////////////////////', product_id, image_url)
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content)).convert('RGB')
        img.thumbnail((width, height), Image.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format='WEBP', quality=80)
        buffer.seek(0)

        product = Product.objects.get(id=product_id)
        product.thumbnail.save(f'{product.sku}_thumb.webp', ContentFile(buffer.read()), save=True)

    except Exception as e:
        # pass
        # Log or handle error
        print(f"Thumbnail generation failed: {e}")


@shared_task 
def orchestrate_allegro_labels(batch_id, order_ids):

    g = group( 
        process_allegro_order.s(batch_id,order_id) 
        for order_id in order_ids 
        )

    # callback: finalize ZIP 
    chord(g)(finalize_batch_zip.s(batch_id))

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3) 
def process_allegro_order(self, batch_id, orderId):  # Celery przekaże self (bo bind=True)
    """ Zwraca dict z wynikiem: 
    { 
        "order_id": ..., 
        "success": True/False, 
        "error": "...", 
        "label_filename": 
        "label_123.pdf" lub None 
    } 
    """ 

    zip_buffer = io.BytesIO() # in‑memory ZIP 
    zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)

    errors = set()
    order = AllegroOrder.objects.filter(order_id=orderId, type='READY_FOR_PROCESSING').first()

    batch = AllegroBatch.objects.get(id=batch_id)
    batch.processed_orders += 1
    batch.save(update_fields=["processed_orders"])


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
    # if not courier:
    #     self.message_user(requests.request, f"⚠️ Nie znaleziono kuriera {courier_name} dla zamówienia {order.order_id}", level='error')
    #     continue

    print('Processing Allegro order in Celery task...', order.order_id)



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

    labels = []   # lista wszystkich etykiet   
    
    for item in items:
        print(' _*__*__*__*__*__*_ Processing item _*__*__*__*__*__*_ ', item.product.sku, item.quantity)
        product = item.product 
        product_girth = check_girth(float(product.depth), float(product.width), float(product.height))
        product_volume = check_volume(float(product.depth), float(product.width), float(product.height))

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
        #@
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

        # print(f"******************* ETAP PRZED PRZEKROCZENIEM: Wymiary {item_l}x{item_h}x{item_w} cm, Waga: {item_weight} kg, Objętość: {item_volume} cm3 przy dopuszczalnych wymiarach: {max_l}x{max_h}x{max_w} cm ************************")

        #@
        if item_l >= max_l or item_h >= max_h or item_w >= max_w or item_weight > max_weight or item_volume > max_volume or item_girth > max_girth:

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
            if resp.status_code in (200, 201):
                re_filename, re_pdf_bytes = create_label(order, ALLEGRO_API_URL, resp, order.vendor, headers, errors, zip_file)

                if re_filename and re_pdf_bytes:
                    labels.append({
                        "filename": re_filename,
                        "pdf": re_pdf_bytes
                    })


            else:
                # self.message_user(request, f"⚠️ Błąd tworzenia przesyłki allegro dla zamówienia {order.order_id} u sprzedawcy {vendor.name}: {resp.status_code} - {resp.text}", level='error')
                order.error = f"❌ 1765 {resp.status_code} - {resp.json().get('errors', [{}])[0].get('userMessage')}\n"
                order.save(update_fields=['error'])
                # print('######################## Error creating shipment ######################## ', resp.status_code, resp.text )
                continue

    # print('######################## Final package to be sent ######################## ', packages)

    resp = create_shipment(ALLEGRO_API_URL, order.vendor, order, packages)
    print('Creating shipment resp ----------------', resp, resp.text)
    if resp.status_code in (200, 201):
        filename, pdf_bytes = create_label(order, ALLEGRO_API_URL, resp, order.vendor, headers, errors, zip_file)

        if filename and pdf_bytes:
            labels.append({
                "filename": filename,
                "pdf": pdf_bytes
            })

        return {
            "order_id": order.order_id,
            "labels": labels,
            "success": len(labels) > 0,
        }

    else:
        print('######################## Error creating shipment ######################## ', resp.status_code, resp.text )
        # self.message_user(request, f"⚠️ Błąd tworzenia przesyłki allegro dla zamówienia {order.order_id} u sprzedawcy {vendor.name}: {resp.status_code} - {resp.text}", level='error')
        order.error = f"❌ 1765 {resp.status_code} - {resp.json().get('errors', [{}])[0].get('userMessage')}\n"
        order.save(update_fields=['error'])
        

@shared_task
def finalize_batch_zip(results, batch_id):

    batch = AllegroBatch.objects.get(id=batch_id)

    buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)

    # for r in results:
    #     if r["filename"] and r["pdf"]:
    #         zip_file.writestr(r["filename"], r["pdf"])
    for result in results:
        for label in result["labels"]:
            zip_file.writestr(label["filename"], label["pdf"])


    zip_file.close()

    # zapis ZIP do modelu
    batch.zip_file.save(
        f"batch_{batch.id}.zip",
        ContentFile(buffer.getvalue())
    )

    batch.status = "SUCCESS"
    batch.save(update_fields=["zip_file", "status"])

    eta_time = timezone.now() + timedelta(days=30)
    delete_batch.apply_async((batch_id,), eta=eta_time)


@shared_task
def delete_batch(batch_id):
    AllegroBatch.objects.filter(batch_id=batch_id).delete()
    return True



# AKTUALIZACJA PRODUKTÓW W ALLEGRO - CELERY TASK

@shared_task
def orchestrate_allegro_updates(action, batch_id, product_ids, user_id):

    if action == 'update_products':

        g = group(
            update_single_product.s(batch_id, product_id, user_id)
            for product_id in product_ids
        )

        chord(g)(finalize_update_batch.s(batch_id))

    else:
        g = group(
            post_single_product.s(batch_id, product_id, user_id)
            for product_id in product_ids
        )

        chord(g)(finalize_update_batch.s(batch_id))


@shared_task
def update_single_product(batch_id, product_id, user_id):

    product = Product.objects.get(id=product_id)
    vendors = Vendor.objects.filter(user_id=user_id, marketplace="allegro.pl")

    updates = []   # lista zmian wykonanych dla tego produktu

    for vendor in vendors:
        headers = {
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Content-Type': 'application/vnd.allegro.public.v1+json',
            'Accept-Language': 'pl-PL',
            'Authorization': f'Bearer {vendor.access_token}'
        }

        url = f"https://{ALLEGRO_API_URL}/sale/offers?external.id={product.sku}&publication.status=ACTIVE"
        offers = allegro_request('GET', url, vendor.name, headers=headers)

        for offer in offers.json().get("offers", []):
            if offer['sellingMode']['price']['amount'] != str(product.price_brutto):
                action = 'price_brutto'
            elif offer['stock']['available'] != product.stock_qty:
                action = 'stock_qty'
            elif offer['name'] != product.title:
                action = 'title'
            else:
                action = 'other'

            edit_url = f"https://{ALLEGRO_API_URL}/sale/product-offers/{offer['id']}"

            resp = action_with_offer_from_product(
                None, 'PATCH', product, edit_url,
                vendor.access_token, vendor.name,
                producer=None, action=action
            )

            if resp.status_code == 200:
                updates.append(action)

            # aktualizacja batcha
            batch = AllegroProductBatch.objects.get(id=batch_id)
            batch.processed_products += 1
            batch.total_products += 1 
            batch.save(update_fields=["processed_products", "total_products"])

            # zapis logu
            parsed = parse_allegro_response(resp, action)

            AllegroProductUpdateLog.objects.create(
                batch_id=batch_id,
                product=product,
                updates=[parsed["message"]] if parsed["success"] else [],
                success=parsed["success"],
                error=None if parsed["success"] else parsed["message"]
            )

    return {
        "product_id": product_id,
        "updates": updates,
    }


@shared_task
def post_single_product(batch_id, product_id, user_id):

    # print('allegro_export request.user ----------------', request.user)
    updates = []   # lista zmian wykonanych dla tego produktu
    product = Product.objects.get(id=product_id)
    print('_____*____post_single_product__task__________*_________', product.sku, product.title, product.price_brutto)
    queryset = Product.objects.filter(id=product_id)    
    url = f"https://{ALLEGRO_API_URL}/sale/product-offers"
    vendors = Vendor.objects.filter(user_id=user_id, marketplace="allegro.pl")
    action="Wystawiono produkt w katalogu Allegro"

    for vendor in vendors:
        product_vendors = product.vendors.all()
        if vendor in product.vendors.all():
            if product.allegro_in_stock and product.allegro_status == 'ACTIVE' and product.vendor == vendor:
                print('___post_single_product__task__ product już istnieje ----------------', vendor, product.sku)
                updates.append('Produkt już jest aktywny w Allegro u tego sprzedawcy.')
            else:
                print('___post_single_product__task__ vendor in product_vendors ----------------', vendor)
                access_token = vendor.access_token
                producer = responsible_producers(access_token, vendor.name)
                resp = action_with_offer_from_product(
                    None, 'POST', product, url,
                    vendor.access_token, vendor.name,
                    producer=producer, action='create'
                )

                print('______________post_single_product response _______________', resp.status_code, resp.text)
                if resp.status_code == 201:
                    product.allegro_in_stock = True
                    product.allegro_status = 'ACTIVE'
                    product.allegro_id = resp.json().get('id')
                    product.save(update_fields=['allegro_in_stock', 'allegro_status', 'allegro_id'])
                    updates.append(action)
                elif resp.status_code == 422 and resp.json().get('errors', [{}])[0].get('code') == 'MatchingProductForIdNotFoundException':
                    product.allegro_in_stock = False
                    product.allegro_status = 'INACTIVE'
                    product.save(update_fields=['allegro_in_stock', 'allegro_status'])
                    error = resp.json().get('errors', [{}])[0]
                    error_message = error.get('userMessage')
                    updates.append(error_message)

                elif resp.status_code == 200:
                    updates.append(action)

                # aktualizacja batcha
                batch = AllegroProductBatch.objects.get(id=batch_id)
                batch.processed_products += 1
                # batch.total_products += 1 
                batch.save(update_fields=["processed_products", "total_products"])

                # zapis logu
                parsed = parse_allegro_response(resp, action)

                AllegroProductUpdateLog.objects.create(
                    batch_id=batch_id,
                    product=product,
                    updates=[parsed["message"]] if parsed["success"] else [],
                    success=parsed["success"],
                    error=None if parsed["success"] else parsed["message"]
                )

    return {
        "product_id": product_id,
        "updates": updates,
    }


@shared_task
def finalize_update_batch(results, batch_id):

    batch = AllegroProductBatch.objects.get(id=batch_id)
    batch.status = "SUCCESS"
    batch.save(update_fields=["status"])

    # Usuń batch + logi po 5 sekundach
    eta_time = timezone.now() + timedelta(days=1)
    delete_batch_and_logs.apply_async((batch_id,), eta=eta_time)

    return True


@shared_task
def delete_batch_and_logs(batch_id):
    AllegroProductUpdateLog.objects.filter(batch_id=batch_id).delete()
    AllegroProductBatch.objects.filter(id=batch_id).delete()
    return True


def responsible_producers(access_token, name):

    url = f"https://{ALLEGRO_API_URL}/sale/responsible-producers" 

    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }

    # response = requests.request("GET", url, headers=headers)

    response = allegro_request("GET", url, name, headers=headers) # params={"limit": 10}
    
    # print('create_offer_from_product response ----------------', response.text)
    return response.json()


################### SEO TITLE GENERATION TASK ###################

@shared_task
def orchestrate_seo_title_batch(batch_id, product_ids):

    if not product_ids:
        finalize_seo_title_batch.delay([], batch_id)
        return

    g = group(
        generate_single_seo_title.s(batch_id, pid)
        for pid in product_ids
    )
    chord(g)(finalize_seo_title_batch.s(batch_id))


@shared_task
def generate_single_seo_title(batch_id, product_id):

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        SeoTitleLog.objects.create(
            batch_id=batch_id,
            product_id=product_id,
            success=False,
            error="Product not found"
        )
        return

    try:
        new_title = generate_allegro_seo_title(product.title)
        product.title = new_title
        product.save(update_fields=["title"])

        SeoTitleLog.objects.create(
            batch_id=batch_id,
            product=product,
            new_title=new_title,
            success=True
        )

        # update batch progress
        batch = SeoTitleBatch.objects.get(id=batch_id)
        batch.processed_products += 1
        batch.save(update_fields=["processed_products"])

    except Exception as e:
        SeoTitleLog.objects.create(
            batch_id=batch_id,
            product=product,
            success=False,
            error=str(e)
        )
    
    return {
        "product_id": product_id,
    }

@shared_task
def finalize_seo_title_batch(results, batch_id):
    batch = SeoTitleBatch.objects.get(id=batch_id)
    batch.status = "SUCCESS"
    batch.save(update_fields=["status"])

    # Usuń batch + logi po 5 sekundach
    eta_time = timezone.now() + timedelta(days=1)
    delete_title_batch_and_logs.apply_async((batch_id,), eta=eta_time)

    return True


@shared_task
def delete_title_batch_and_logs(batch_id):
    SeoTitleLog.objects.filter(batch_id=batch_id).delete()
    SeoTitleBatch.objects.filter(id=batch_id).delete()
    return True