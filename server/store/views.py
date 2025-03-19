import json
import os
import re
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework import generics, status
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from store.tasks import store_product_images

from vendor.models import Vendor

from .serializers import CartCheckSerializer, ProductSerializer, IconProductSerializer, CategorySerializer, GallerySerializer, CartSerializer, DeliveryCouriersSerializer, CartOrderSerializer, CartOrderItemSerializer, ReturnOrderItemSerializer
from .models import Category, Product, Cart, User, CartOrder, DeliveryCouriers, Gallery, CartOrderItem, ReturnItem
from .store_pagination import StorePagination

from decimal import Decimal, InvalidOperation
import stripe
import shortuuid
import pandas as pd

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

import requests
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile

stripe.api_key = os.environ.get("STRIPE_API_KEY")

class CategoriesView(generics.ListAPIView):

    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = (AllowAny, )


# @method_decorator(cache_page(60 * 60 * 2, cache="default"), name="dispatch")
class ProductsView(generics.ListAPIView):

    serializer_class = IconProductSerializer
    queryset = Product.objects.all()
    pagination_class = StorePagination
    permission_classes = (AllowAny, )


class DeleteProductsView(APIView):
    permission_classes = (AllowAny, )

    def delete(self, request):
        Product.objects.all().delete()

        return Response({
            "message": "All products has been deleted!"
        })


@method_decorator(cache_page(60 * 60 * 2, cache="default"), name="dispatch")
class ProductDetailsView(APIView):

    ''' context={'request': request} - is nessecary to return
        full url(with domain) in image filed in response
    '''

    permission_classes = (AllowAny, )

    def get(self, request, id):
        product = get_object_or_404(Product, id=id)
        gallery = product.gallery()
        product_image = product.image
        product_image_gallery = [{
            'image': product_image,
            'active': True,
            'date': product.date,  # or use the correct date field for the product
            'gid': 'product_image',  # A placeholder or a specific identifier
        }]
        combined_gallery = product_image_gallery + list(gallery)
        
        serializer = ProductSerializer(product, context={'request': request})
        gallery_serializer = GallerySerializer(combined_gallery, many=True, context={'request': request})
        return Response({
            "product": serializer.data,
            "gallery": gallery_serializer.data,
        })
    

@method_decorator(cache_page(60 * 60 * 2, cache="default"), name="dispatch")
class ProductsByCat(APIView):
    
    permission_classes = (AllowAny, )

    def get(self, request, id):
        category = get_object_or_404(Category, id=id)
        products = Product.objects.filter(category=category)      
        prod_serializer = ProductSerializer(products, many=True, context={'request': request})
        cat_serializer = CategorySerializer(category, context={'request': request})
        return Response({
            "products": prod_serializer.data,
            "category": cat_serializer.data,
        })
    

class AddToCardView(APIView):

    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        user = User.objects.get(id=user_id)
        product_id = request.data['product_id']
        quantity = request.data['quantity']
        product = Product.objects.get(id=product_id)
        cart, created = Cart.objects.get_or_create(
                user=user,
                product=product,
            )
        cart.qty = quantity
        cart.price = product.price
        cart.sub_total = cart.qty * cart.price
        cart.total = (
            cart.sub_total + 
            (cart.shipping_amount or Decimal('0.00')) + 
            (cart.service_fee or Decimal('0.00')) + 
            (cart.tax_fee or Decimal('0.00'))
        )
        cart.save()

        cart_serializer = CartSerializer(cart)

        return Response({
            "product_id": product_id,
            "cart": cart_serializer.data,
        })
    
    

class CartView(APIView):

    permission_classes = (AllowAny, )

    def get(self, request, id):
        cart = Cart.objects.filter(user__id=id)
        cart_serializer = CartSerializer(cart, many=True, context={'request': request})

        return Response({
            "cart": cart_serializer.data,
        })
    
    def put(self, request, *args, **kwargs):
        cart_id = request.data['cart_id']
        quantity = request.data['quantity']
        cart = Cart.objects.get(id=cart_id)
        cart.qty = quantity
        cart.sub_total = cart.qty * cart.price
        cart.total = (
            cart.sub_total + 
                (cart.shipping_amount or Decimal('0.00')) + 
                (cart.service_fee or Decimal('0.00')) + 
                (cart.tax_fee or Decimal('0.00'))
            )
        cart.save()

        print('CartView - put', cart.product.title)

        cart_serializer = CartSerializer(cart, context={'request': request})

        return Response({
            # "product_id": product_id,
            "cart": cart_serializer.data,
        })
    
    def delete(self, request, id):
        cart = Cart.objects.get(id=id)
        cart.delete()

        return Response({
            "message": "Cart has been deleted!",
        })
    

class CartCountView(APIView):

    permission_classes = (AllowAny, )

    def get(self, request, id):
        cart_count  = Cart.objects.filter(user__id=id).count()
        return Response({
            "cart_count ": cart_count ,
        })
    

class CreateOrderView(APIView):

    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        full_name = request.data['full_name']
        email = request.data['email']
        mobile = request.data['mobile']
        street = request.data['street']
        number = request.data['number']
        post_code = request.data['post_code']
        city = request.data['city']
        sub_total = request.data['sub_total']
        shipping_amount = request.data['shipping_amount']
        total = request.data['total']
        delivery = request.data['delivery']

        user = User.objects.get(id=user_id)
        order = CartOrder(
            buyer=user,
            full_name=full_name,
            email=email,
            mobile=mobile,
            street=street,
            number=number,
            post_code=post_code,
            city=city,
            sub_total=sub_total,
            shipping_amount=shipping_amount,
            total=total,
            delivery=delivery,
        )
        order.payment_status = "processing"
        order.order_status = "Processing"
        order.save()

        order_selializer = CartOrderSerializer(order)

        return Response({
            "order": order_selializer.data,
        })



class DeliveryCouriersView(APIView):

    permission_classes = (AllowAny, )

    def get(self, request):
        couriers = DeliveryCouriers.objects.all()
        couriers_serializer = DeliveryCouriersSerializer(couriers, many=True)

        return Response({
            "couriers": couriers_serializer.data
        })
    

class StripeView(APIView):

    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        print('*****settings.SITE_URL**********', settings.SITE_URL)
        order_oid = request.data['order_oid']
        order = get_object_or_404(CartOrder, oid=order_oid)
        order.payment_status = "pending"
        order.order_status = "Pending"
        order.save()

        try:
            checkout_session = stripe.checkout.Session.create(
               customer_email=order.email,
               payment_method_types=['card'],
               line_items=[
                   {
                       'price_data': {
                           'currency': 'usd',
                           'product_data': {
                               'name': order.full_name,
                           },
                           'unit_amount': int(order.total * 100),
                       },
                       'quantity': 1,
                   }
               ],
               mode='payment',
                # success_url=settings.SITE_URL+'/payment-success/'+ str(order.oid) +'?session_id={CHECKOUT_SESSION_ID}',
                # cancel_url=settings.SITE_URL+'/?session_id={CHECKOUT_SESSION_ID}',
                success_url = f"{settings.SITE_URL}/payment-success?order_id={order.oid}&buyer={order.buyer.id}&session_id={{CHECKOUT_SESSION_ID}}&user={order.buyer.id}",
                cancel_url=f"{settings.SITE_URL}/payment-failed?order_id={order.oid}&buyer={order.buyer.id}&session_id={{CHECKOUT_SESSION_ID}}",
            )
            order.stripe_session_id = checkout_session.id 
            order.save()

            # return redirect(checkout_session.url)
            return Response({
                "checkout_session": checkout_session.url
            })
        except stripe.error.StripeError as e:
            order.payment_status = "cancelled"
            order.order_status = "Cancelled"
            order.save()
            return Response( {'error': f'Something went wrong when creating stripe checkout session: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class FinishedCartOrderView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        oid = request.data["oid"]
        user_id = request.data["user_id"]
        user = User.objects.get(id=user_id)
        print("********************** FinishedCartOrderView *********************", oid, user_id)
        order = CartOrder.objects.get(oid=oid)
        order.payment_status = "Zapłacone"
        order.order_status = "Czeka na Etykietę"
        order.save()

        cart = Cart.objects.filter(user=user)
        for item in cart:
            CartOrderItem.objects.create(
                order=order,
                product=item.product,
                qty=item.qty,
                price=item.price,
                )
            
        cart.delete()

        return Response({
            "message": "Order is Paid and status is Fulffield",
        })
    

class CartOrderItemView(generics.ListAPIView):
    
    serializer_class = CartOrderSerializer
    queryset = CartOrder.objects.all()
    permission_classes = (AllowAny, )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        # Add choices to response
        response.data["return_reasons"] = ReturnItem.RETURN_REASONS
        return response


class ReturnProductView(APIView):
    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        print('******************ReturnProductView', request.data)  
        user_id = request.data['userId']
        oid = request.data['orderId']
        prod_id = request.data['prodId']
        qty = request.data['qty']
        return_reason = request.data['returnReason']
        # print('******************ReturnProductView orderId', oid)
        # print('******************ReturnProductView prod_id', prod_id)
        # print('******************ReturnProductView qty', qty)

        user = get_object_or_404(User, id=user_id)
        order = get_object_or_404(CartOrder, oid=oid)
        product = get_object_or_404(Product, id=prod_id)

        order_item = CartOrderItem.objects.get(
            order=order,
            product=product,
        )
        order_item.return_qty=qty
        order_item.initial_return=True
        order_item.return_reason=return_reason
        order_item.save()

        return_item = ReturnItem.objects.create(
            user=user,
            order=order,
            order_item=order_item,
            product=product,
            price=order_item.price,
            qty=qty,
            return_reason=return_reason,
        )

        return_item_srlz = ReturnOrderItemSerializer(return_item)

        return Response({
            # "oid": oid,
            # "prod_id": prod_id,
            "return_item": return_item_srlz.data,
            # "order_item": order_item,
        })
    

class UsersReturns(APIView):

    # serializer_class = ReturnOrderItemSerializer
    # queryset = ReturnItem.objects.all()
    permission_classes = (AllowAny, )

    def post(self, request):
        user_id = request.data['userId']
        user = get_object_or_404(User, id=user_id)
        returns = ReturnItem.objects.filter(user=user)
        serializer = ReturnOrderItemSerializer(returns, many=True)

        return Response({
            'returns': serializer.data
        })

    

class ProductCSVView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        user_id = request.data["user_id"]
        # print('ProductCSVView', user_id)
        user = User.objects.get(id=user_id)
        vendor = get_object_or_404(Vendor, user=user)
        if not csv_file:
            return Response({"error": "No file uploaded"}, status=400)
        
        def safe_decimal(value):
            try:
                return Decimal(value)
            except InvalidOperation:
                return Decimal('0.00')

        try:
            file_extension = os.path.splitext(csv_file.name)[1].lower()

            if file_extension == ".csv":
                df = pd.read_csv(csv_file, encoding="utf-8", keep_default_na=False)
            elif file_extension in [".xls", ".xlsx", ".xlsm"]:
                df = pd.read_excel(csv_file, engine="openpyxl", sheet_name='Szablon', keep_default_na=False)
                # sheets = pd.ExcelFile(csv_file, engine="openpyxl").sheet_names
                # print('**************SHEETS*****************', sheets)
            else:
                return Response({"error": "Unsupported file format"}, status=400)

            for index, row in df.iterrows():
                # print('***PANDAS-ROW-SKU***', row[7])
                if row.iloc[7] == 'Aktywna':
                    # print('***PANDAS-ROW-SKU***', row.to_dict())

                    # print('***PANDAS-ROW-title***', row[21])
                    # print('***PANDAS-ROW-SKU***', row[11])
                    # print('***PANDAS-ROW-stock_qty***', row[12])
                    # print('***PANDAS-ROW-price***', row[14])

                    category = row.iloc[10].split('>')
                    for cat in category:
                        clean_cat = re.sub(r"\s*\(\d+\)", "", cat).strip()

                    # print('***PANDAS-ROW***', clean_cat)

                    # DESCR
                    descr = []
                    matching_columns = [col for col in df.columns if str(col).startswith("86275")]
                    if matching_columns:
                        for col in matching_columns:
                            try:
                                data = json.loads(row[col])  # Convert JSON string to a Python dictionary
                                for section in data.get("sections", []):
                                    for item in section.get("items", []):
                                        if item.get("type") == "TEXT":  # Extract only text content
                                            # print(f'***PANDAS-ROW-TEXT***', item.get("content", ""))
                                            descr.append(item.get("content", ""))
                            except json.JSONDecodeError:
                                print(f'Error decoding JSON for column {col}')

                    # print(f'***PANDAS-ROW-TEXT***', descr)
                    # print('----------------------------------------------',)
                    # print('##############################################',)
                    # print('----------------------------------------------',)


                    img_links = []
                    links = row.iloc[22].split('|') #15
                    for link in links:
                        img_links.append(f"{link.strip()},")

                        # print('***PANDAS-ROW***IMAGE', link.strip())
                    # print('***PANDAS-ROW***IMAGE', img_links)
                    # print('----------------------------------------------',)
                    # print('##############################################',)
                    # print('----------------------------------------------',)


                    category_, created = Category.objects.get_or_create(
                        title=clean_cat,
                        # slug=clean_cat.replace(" ", "-").lower() + "-" + shortuuid.uuid()[:4],
                    )       
                    # print('***PANDAS-ROW-category_***', category_) 
                    # print('***USER***', user) 
                    product, created_product = Product.objects.get_or_create(
                        title=row.iloc[21],
                        img_links=img_links,
                        description=descr,
                        price=safe_decimal(row.iloc[14]),
                        stock_qty=row.iloc[12],
                        sku=row.iloc[11],
                        shipping_amount=safe_decimal(14.99),
                        category=category_,
                        vendor=vendor,
                    )

            return Response({"message": "CSV processed successfully"}, status=201)
        except Exception as e:
            # Log full error and traceback
            import traceback
            error_message = traceback.format_exc()
            print(f"Error: {error_message}")
            return Response({"error": str(e)}, status=500)
        

class LinksToGallery(APIView):

    permission_classes = (AllowAny,)

    def post(self, request):

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

        try:
            products = Product.objects.all()

            for product in products:
                img_links = product.img_links

                if not img_links:
                    return f"No images found for product {product.id}"

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
                    else:
                        print('########### RESPONSE NOT 200', response.status_code)

            return Response({
                "message": f"Images for products stored successfully"
            })

        except Product.DoesNotExist:
             return Response({
                    "message": f"Product {product.id} does not exist"
                })
        except Exception as e:
            return Response({
                    "message": f"Error: {str(e)}"
                })
