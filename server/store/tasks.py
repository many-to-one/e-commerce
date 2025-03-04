import requests
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from celery import shared_task
from .models import Product, Gallery

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
    try:
        product = Product.objects.get(id=product_id)
        # img_links = product.img_links

        if not img_links:
            return f"No images found for product {product_id}"

        for index, img_url in enumerate(img_links):
            response = requests.get(img_url.strip(), timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img = img.convert("RGB")  # Convert to RGB to avoid format issues
                
                # Compress image
                compressed_img = compress_image(img)

                # Save first image as `product.image`
                if index == 0:
                    product.image.save(f"product_{product.id}.jpg", ContentFile(compressed_img.read()), save=True)
                else:
                    # Save the rest as gallery images
                    gallery_img = Gallery(product=product)
                    gallery_img.image.save(f"gallery_{product.id}_{index}.jpg", ContentFile(compressed_img.read()), save=True)

        return f"Images for product {product_id} stored successfully"

    except Product.DoesNotExist:
        return f"Product {product_id} does not exist"
    except Exception as e:
        return f"Error: {str(e)}"
