import requests
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from celery import shared_task
from .models import ClientAccessLog, Product, Gallery

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
    username = data.get('username', 'Anonymous')
    user_agent = data['user_agent'].lower()
    user = data.get('user', None)
    print('Celery user++++++++++++++++++++', user)

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
        user=username,
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
        print('############################ get_geo_from_ip ############################', data)
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
    print('Test celery task running.../////////////////////////////////', x + y)
    return x + y

@shared_task
def generate_thumbnail(product_id, image_url, width=200, height=200):
    print('Generating thumbnail for////////////////////////////////////////////', product_id, image_url)
    # try:
    #     response = requests.get(image_url, timeout=10)
    #     response.raise_for_status()

    #     img = Image.open(BytesIO(response.content)).convert('RGB')
    #     img.thumbnail((width, height), Image.LANCZOS)

    #     buffer = BytesIO()
    #     img.save(buffer, format='WEBP', quality=80)
    #     buffer.seek(0)

    #     product = Product.objects.get(id=product_id)
    #     product.thumbnail.save(f'{product.sku}_thumb.webp', ContentFile(buffer.read()), save=True)

    # except Exception as e:
    #     # pass
    #     # Log or handle error
    #     print(f"Thumbnail generation failed: {e}")