import json
import os
import re
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.urls import path
from django import forms

from rest_framework import generics, status
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .tasks import generate_thumbnail, orchestrate_allegro_updates, sync_selected_offers_task, test
from django.http import HttpResponse

from .utils.payu import get_client_ip, payu_authenticate, to_grosze
from vendor.models import Vendor
from vendor.serializer import VendorSerializer

from .serializers import CartCheckSerializer, PrestaCSVSerializer, ProductSerializer, IconProductSerializer, CategorySerializer, GallerySerializer, CartSerializer, DeliveryCouriersSerializer, CartOrderSerializer, CartOrderItemSerializer, ReturnOrderItemSerializer, AddressSerializer
from .models import AllegroProductBatch, Category, Invoice, Product, Cart, User, CartOrder, DeliveryCouriers, Gallery, CartOrderItem, ReturnItem, Address
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

import httpx
import asyncio


stripe.api_key = os.environ.get("STRIPE_API_KEY")
PAYU_CLIENT_ID = os.environ.get("PAYU_CLIENT_ID")
PAYU_CLIENT_SECRET = os.environ.get("PAYU_CLIENT_SECRET")
PAYU_OAUTH_URL = os.environ.get("PAYU_OAUTH_URL")
PAYU_API_URL = os.environ.get("PAYU_API_URL")
SITE_URL = os.environ.get("SITE_URL")
continueUrl = os.environ.get("continueUrl")
_marketplace = os.environ.get("marketplace")
WEB_VENDOR = os.environ.get("WEB_VENDOR")
# WEB_VENDOR_EMAIL = os.environ.get("WEB_VENDOR_EMAIL")
# WEB_VENDOR_PHONE = os.environ.get("WEB_VENDOR_PHONE")
VENDOR_1 = os.environ.get("VENDOR_1")

class CategoriesView(generics.ListAPIView):

    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = (AllowAny, )


# # @method_decorator(cache_page(60 * 60 * 2, key_prefix="products_list", cache="default"), name="dispatch")
# class ProductsView(generics.ListAPIView):

#     serializer_class = IconProductSerializer
#     queryset = Product.objects.all()
#     pagination_class = StorePagination
#     permission_classes = (AllowAny, )


class VendorContact(generics.ListAPIView): #RetrieveAPIView

    serializer_class = VendorSerializer
    permission_classes = (AllowAny, )

    def get_queryset(self):
        user = User.objects.get(is_superuser=True)
        print(user)
        queryset = Vendor.objects.filter(user=user, marketplace=_marketplace)
        print(queryset)
        return queryset



# @method_decorator(cache_page(60 * 5), name='dispatch') # 5 min cache
class ProductsView(generics.ListAPIView):
    serializer_class = IconProductSerializer
    pagination_class = StorePagination
    permission_classes = (AllowAny, )

    def get_queryset(self):
        vendor = Vendor.objects.filter(user=self.request.user, marketplace=_marketplace)
        queryset = Product.objects.filter(
            in_stock=True,
            stock_qty__gt=0,
            vendor=vendor,
            )
        # queryset = Product.objects.all()
        search = self.request.query_params.get('search')
        # print(' ***************** get queryset ++++++++++++++', search)
        if search:
            queryset = queryset.filter(title__icontains=search)  # or other fields
        return queryset


class PopularProductsView(generics.ListAPIView):

    serializer_class = IconProductSerializer
    pagination_class = StorePagination
    permission_classes = (AllowAny, )

    def get_queryset(self):
        queryset = Product.objects.filter(
            special_offer=True, 
            in_stock=True,
            stock_qty__gt=0,
            )
        return queryset
    

class DiscountProductsView(generics.ListAPIView):

    serializer_class = IconProductSerializer
    pagination_class = StorePagination
    permission_classes = (AllowAny, )

    def get_queryset(self):
        queryset = Product.objects.filter(
            hot_deal=True,
            in_stock=True,
            stock_qty__gt=0,
            )
        return queryset
    

class NewsProductsView(generics.ListAPIView):

    serializer_class = IconProductSerializer
    pagination_class = StorePagination
    permission_classes = (AllowAny, )

    def get_queryset(self):
        queryset = Product.objects.filter(
            featured=True,
            in_stock=True,
            stock_qty__gt=0,
            )
        return queryset


class DeleteProductsView(APIView):
    permission_classes = (AllowAny, )

    def delete(self, request):
        Product.objects.all().delete()

        return Response({
            "message": "All products has been deleted!"
        })


# @method_decorator(cache_page(60 * 60 * 2, cache="default"), name="dispatch")
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
    

class ProductsByCat(generics.ListAPIView):
    serializer_class = IconProductSerializer
    pagination_class = StorePagination
    permission_classes = (AllowAny,)

    def get_queryset(self):
        category_id = self.kwargs["id"]
        category = get_object_or_404(Category, id=category_id)
        return Product.objects.filter(
            category=category, 
            in_stock=True,
            stock_qty__gt=0,
            )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        category = get_object_or_404(Category, id=self.kwargs["id"])
        response.data["category"] = CategorySerializer(
            category, context={"request": request}
        ).data
        return response
    

class ProductsBySubCat(generics.ListAPIView):
    serializer_class = IconProductSerializer
    pagination_class = StorePagination
    permission_classes = (AllowAny,)

    def get_queryset(self):
        from django.db.models import Q
        sub_cat = self.kwargs["sub_cat"]
        # products = Product.objects.filter(
        #     Q(sub_cat__icontains=sub_cat),
        #     )
        products = Product.objects.filter(
            in_stock=True,
            stock_qty__gt=0,
            sub_cat__icontains=sub_cat
        )

        return products

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # category = get_object_or_404(Category, sub_cat=self.kwargs["sub_cat"])
        # response.data["category"] = CategorySerializer(
        #     category, context={"request": request}
        # ).data
        return response



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


def payu_authenticate():
    auth_url = PAYU_OAUTH_URL
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": PAYU_CLIENT_ID,  # Replace with your actual client_id
        "client_secret": PAYU_CLIENT_SECRET  # Replace with your actual client_secret
    }

    try:
        auth_response = requests.post(auth_url, data=auth_data)
        # auth_response.raise_for_status()
        token_data = auth_response.json()
        print('*****payu_authenticate Token Data**********', token_data)
        access_token = token_data.get("access_token")
        if not access_token:
            return None
        return access_token
    except requests.RequestException as e:
        return None

# from decimal import Decimal
# def to_grosze(value):
#     if isinstance(value, Decimal):
#         return int(value * 100)
#     return int(float(value) * 100)

# def get_client_ip(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]  # First IP in list
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip


class PayUView(APIView):

    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        # print('****************** PAYU_CLIENT_ID *************************', PAYU_CLIENT_ID)
        vendor = Vendor.objects.get(marketplace=_marketplace)
        order_oid = request.data['order_oid']
        order = get_object_or_404(CartOrder, oid=order_oid)
        cart = Cart.objects.filter(user=order.buyer)
        for item in cart:
            CartOrderItem.objects.create(
                order=order,
                product=item.product,
                qty=item.qty,
                price=item.price,
                )
        # print('*****PayUView**********', order.sub_total, order.total)
        # print('*****PayUView Order Items**********', order.get_order_items())
        
        products = order.get_order_items()
        products_arr = []
        for product in products:
            # print('*****product**********', product)
            # print('*****product-title**********', product.product.title)
            # print('*****product-price**********', product.price)
            # print('*****product-qty**********', product.qty)
            products_arr.append({
                "name": product.product.title,
                "unitPrice": to_grosze(product.price),
                "quantity": product.qty,
            })
        

        payload = {
            
            "continueUrl": continueUrl,
            "customerIp": get_client_ip(request), #"127.0.0.1",
            "merchantPosId": PAYU_CLIENT_ID,
            "description": "Zabawki dla dzieci",
            "currencyCode": "PLN",
            "totalAmount": f"{to_grosze(order.total)}",
            "products": products_arr
        }

        # print('*****payload**********', payload)

        # Step 2: Forward order to PayU
        payu_url = f"{PAYU_API_URL}/orders"
        access_token = payu_authenticate() # 'try payu from .env for test'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        # # Step 2: Forward order to PayU
        # payu_url = f"{PAYU_API_URL}/orders"
        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": f"Bearer {vendor.access_token}"
        # }

        response = requests.post(payu_url, json=payload, headers=headers, allow_redirects=False)
        print('*****PayUView Order Response**********', response.status_code, response.text)

        payu_response = response.json()
        redirect_url = payu_response.get("redirectUri")
        order_id = payu_response.get("orderId")
        print('*****PayUView Redirect URL**********', redirect_url)

        if response.status_code == 302 or response.status_code == 201:
            order.payu_order_id = order_id
            order.save()
            return Response({
                "status": 200,
                "redirect_url": redirect_url
                })
        if response.status_code == 401:
            new_access_token = payu_authenticate()
            if new_access_token:
                vendor.access_token = new_access_token
                vendor.save()
                headers["Authorization"] = f"Bearer {new_access_token}"
                response = requests.post(payu_url, json=payload, headers=headers, allow_redirects=False)
                payu_response = response.json()
                redirect_url = payu_response.get("redirectUri")
                order_id = payu_response.get("orderId")
                print('*****RE-PayUView Redirect URL**********', redirect_url)
                if response.status_code == 302 or response.status_code == 201:
                    order.payu_order_id = order_id
                    order.save()
                    return Response({
                        "status": 200,
                        "redirect_url": redirect_url
                        })
            else:
                return Response({"error": "Re-authentication failed"}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({ 'status': 'test' })
    

class StripeView(APIView):

    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        
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
        cart.delete()

        return Response({
            "message": "Order is Paid and status is Fulffield",
        })
    

# class CartOrderItemView(generics.ListAPIView):
    
#     serializer_class = CartOrderSerializer
#     queryset = CartOrder.objects.all()
#     permission_classes = (AllowAny, )

#     def list(self, request, *args, **kwargs):
#         response = super().list(request, *args, **kwargs)

#         # Add choices to response
#         response.data["return_reasons"] = ReturnItem.RETURN_REASONS
#         return response


class CartOrderItemView(generics.ListAPIView):
    serializer_class = CartOrderSerializer
    permission_classes = (AllowAny,)  # later you can change to IsAuthenticated

    def get_queryset(self):
        user = self.request.user

        # If user is authenticated — filter by buyer
        if user.is_authenticated:
            return CartOrder.objects.filter(buyer=user)

        # If anonymous — return none or all depending on your logic
        return CartOrder.objects.none()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
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
        price = request.data['price']
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
    

class TestView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        user_id = request.data["user_id"]
        print('TestView - user_id', user_id)
        print('TestView - csv_file', csv_file)

        return Response({
            'returns': "Url is working"
        })
    


class PrestaCSVView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        user_id = request.data["user_id"]
        user = User.objects.get(id=1)

        if Vendor.objects.exists():
            pass
        else:
            return Response({
                    "Error": "No vendor",
                    "Błąd": "Nie ma żadnego sprzedającego",
                    }, 
                    status=404
                )
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
                df = pd.read_csv(csv_file, sep=";", encoding="utf-8", keep_default_na=False)
            else:
                return Response({"error": "Unsupported file format"}, status=400)


            for idx, row in df.iterrows():
                categories = row["Kategorie (x,y,z...)"].split(",")
                if len(categories) >= 2:
                    category_, created = Category.objects.get_or_create(
                        title=categories[1],
                        category_hierarchy=categories[2:]
                    )

                images = str(row["Zdjęcia"]).split(",")
                first_image = images[0].strip() if images else None

                net_price = safe_decimal(row["Cena bez podatku. (netto)"])
                gross_price = net_price * Decimal("1.23")

                print(len(row["Nazwa"]), row["Nazwa"])

                product, created_product = Product.objects.get_or_create(
                    title=row["Nazwa"],
                    ean=row["EAN"],
                    image = first_image,
                    img_links=images,
                    description=row["Opis"],
                    price=gross_price,   # <-- includes 23% VAT
                   # tax_rate=safe_decimal("23.00")
                    hurt_price=safe_decimal(row["Cena hurtowa"]),
                    stock_qty=row["Ilość"],
                    sku=row["Kod dostawcy"],
                    shipping_amount=safe_decimal(9.99),
                    category=category_,
                    sub_cat=categories[2:],
                )
                all_vendors = Vendor.objects.all()
                product.vendors.add(*all_vendors)

                product.save()

            return Response({"message": "CSV processed successfully"}, status=201)

        
        except Exception as e:
            # Log full error and traceback
            import traceback
            error_message = traceback.format_exc()
            print(f"Error: {error_message}")
            return Response({"error": str(e)}, status=500) 
        

from rest_framework.parsers import MultiPartParser, FormParser
class PrestaUpdateCSVView(APIView):

    serializer_class = PrestaCSVSerializer
    permission_classes = (AllowAny,)
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer(self, *args, **kwargs): 
        return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # csv_file = request.FILES.get("file")
        # user_id = request.data["user_id"]
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True) 
        csv_file = serializer.validated_data["file"] 
        user_id = serializer.validated_data["user_id"]
        print('PrestaUpdateCSVView - user_id', user_id)
        user = User.objects.get(id=user_id)
        print('PrestaUpdateCSVView - user', user)

        # sprawdzanie checkboxów
        update_price = request.data.get("price") == "true"
        update_stock = request.data.get("stock") == "true"
        update_description = request.data.get("description") == "true"

        # przykładowe użycie
        # if update_price:
        #     print("Aktualizujemy ceny *******************")
        # if update_stock:
        #     print("Aktualizujemy stany *******************")
        # if update_description:
        #     print("Aktualizujemy opisy*******************")

        # return Response({"message": "CSV proccessed successfully"}, status=201)

        if Vendor.objects.exists():
            pass
        else:
            return Response({
                    "Error": "No vendor",
                    "Błąd": "Nie ma żadnego sprzedającego",
                    }, 
                    status=404
                )
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
                df = pd.read_csv(csv_file, sep=";", encoding="utf-8", keep_default_na=False)
            else:
                return Response({"error": "Unsupported file format"}, status=400)


            for idx, row in df.iterrows():
                # for r in row:
                    # print('***ROW***', r)
                categories = row["Kategorie (x,y,z...)"].split(",")
                if len(categories) >= 2:
                    title = categories[1] 
                    print('***CATEGORY TITLE***', title)
                    hierarchy = categories[2:]
                    print('***CATEGORY HIERARCHY***', hierarchy)
                    # Try to fetch existing category
                    category = Category.objects.filter(title=title).first()
                    print('***EXISTING CATEGORY***', category)
                    if category:  # Update fields
                        if category.category_hierarchy != hierarchy:
                            category.category_hierarchy = hierarchy
                            category.save(update_fields=["category_hierarchy"])
                    else:  # Create new category
                        category = Category.objects.create(
                            title=title,
                            category_hierarchy=hierarchy
                        )

                images = str(row["Zdjęcia"]).split(",")
                first_image = images[0].strip() if images else None

                net_price = safe_decimal(row["Cena bez podatku. (netto)"])
                gross_price = net_price * Decimal("1.23")

                print(len(row["Nazwa"]), row["Nazwa"])

                product = Product.objects.filter(ean=row["EAN"]).first()
                # if product:
                #     if update_stock:
                #         print("Aktualizujemy stany *******************")
                #         product.stock_qty = row["Ilość"]
                #         product.updates = True
                #         product.save(update_fields=['stock_qty', 'updates'])
                #     if update_price:
                #         print("Aktualizujemy ceny *******************")
                #         product.price = gross_price   # <-- includes 23% VAT
                #         # product.hurt_price = safe_decimal(row["Cena hurtowa"])
                #         product.new_hurt_price = safe_decimal(row["Cena hurtowa"])
                #         product.updates = True
                #         product.save(update_fields=['price', 'updates'])

                if product:
                    if update_stock:
                        if product.stock_qty != row["Ilość"]:
                            product.stock_qty = row["Ilość"]
                            product.updates = True
                            product.save(update_fields=['stock_qty', 'updates'])

                    if update_price:
                        new_price = gross_price
                        new_hurt = safe_decimal(row["Cena hurtowa"])

                        fields_to_update = []

                        if product.price != new_price:
                            product.price = new_price
                            fields_to_update.append("price")

                        if product.new_hurt_price != new_hurt:
                            product.new_hurt_price = new_hurt
                            fields_to_update.append("new_hurt_price")

                        if fields_to_update:
                            product.updates = True
                            fields_to_update.append("updates")
                            product.save(update_fields=fields_to_update)


                    # if update_description:
                    #     product.title = row["Nazwa"]
                    #     product.image = first_image
                    #     product.img_links = images
                    #     product.description = row["Opis"]
                    #     product.price = gross_price   # <-- includes 23% VAT
                    #     product.new_hurt_price = safe_decimal(row["Cena hurtowa"])
                    #     product.stock_qty = row["Ilość"]
                    #     product.sku = row["Kod dostawcy"]
                    #     product.shipping_amount = safe_decimal(9.99)
                    #     product.category = category
                    #     product.sub_cat = categories[2:]
                    #     product.updates = True
                    #     # product.tax_rate = safe_decimal("23.00")

                    #     product.save()

                    if update_description:
                        fields_to_update = []

                        title = row["Nazwa"]
                        if product.title != title:
                            product.title = title
                            fields_to_update.append("title")

                        if product.image != first_image:
                            product.image = first_image
                            fields_to_update.append("image")

                        if product.img_links != images:
                            product.img_links = images
                            fields_to_update.append("img_links")

                        desc = row["Opis"]
                        if product.description != desc:
                            product.description = desc
                            fields_to_update.append("description")

                        if product.price != gross_price:
                            product.price = gross_price
                            fields_to_update.append("price")

                        hurt_price = safe_decimal(row["Cena hurtowa"])
                        if product.hurt_price != hurt_price:
                            product.new_hurt_price = hurt_price
                            fields_to_update.append("new_hurt_price")

                        qty = row["Ilość"]
                        if product.stock_qty != qty:
                            product.stock_qty = qty 
                            fields_to_update.append("stock_qty")

                        sku = row["Kod dostawcy"]
                        if product.sku != sku:
                            product.sku = sku
                            fields_to_update.append("sku")

                        shipping = safe_decimal(9.99)
                        if product.shipping_amount != shipping:
                            product.shipping_amount = shipping
                            fields_to_update.append("shipping_amount")

                        if product.category != category:
                            product.category = category
                            fields_to_update.append("category")

                        sub_cat = categories[2:]
                        if product.sub_cat != sub_cat:
                            product.sub_cat = sub_cat
                            fields_to_update.append("sub_cat")

                        if fields_to_update:
                            product.updates = True
                            fields_to_update.append("updates")
                            product.save(update_fields=fields_to_update)
                            print("*******cena hurtowa zaktualizowana********", product.new_hurt_price)

                else:
                    if row["Ilość"] <= 0:
                        continue  # Skip creating product if stock quantity is 0 or less
                    title = row["Nazwa"].strip()
                    if "przecena" not in title.lower():
                        product = Product.objects.create(
                            title=row["Nazwa"],
                            ean=row["EAN"],
                            image=first_image,
                            img_links=images,
                            description=row["Opis"],
                            price=gross_price,   # <-- includes 23% VAT
                            hurt_price=safe_decimal(row["Cena hurtowa"]),
                            stock_qty=row["Ilość"],
                            sku=row["Kod dostawcy"],
                            shipping_amount=safe_decimal(9.99), 
                            category=category,   
                            sub_cat=categories[2:],
                        # tax_rate=safe_decimal("23.00")
                        )

                        all_vendors = Vendor.objects.filter(user=user)
                        product.vendors.add(*all_vendors)
                        product.save()

            updated_products = Product.objects.filter(updates=True)
            product_ids = list(updated_products.values_list("id", flat=True))

            batch = AllegroProductBatch.objects.create(
                status="PENDING",
                total_products=len(product_ids)
            )

            # action="update_products",

            # if update_stock == True and update_price == False and update_description == False:
            #     orchestrate_allegro_updates.delay(
            #         action,
            #         batch.id,
            #         product_ids,
            #         user.id
            #     )

            # return Response({"message": "CSV proccessed successfully"}, status=201)

            return Response({
                "message": "CSV processed successfully",
                "batch_id": batch.id,
                "redirect_url": f"{os.getenv('PRO_SITE_URL')}/api/store/admin/allegroupdatebatch/{batch.id}/status/"
            }, status=201)


        
        except Exception as e:
            # Log full error and traceback
            import traceback
            error_message = traceback.format_exc()
            print(f"Error: {error_message}")
            return Response({"error": str(e)}, status=500) 
        


class ProductCSVView(APIView):

    """ The vendor must be created first!!! """

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        user_id = request.data["user_id"]
        # print('ProductCSVView', user_id)
        user = User.objects.get(id=user_id)

        cat_set = set()

        try:
            vendor = Vendor.objects.get(user=user)
        except:
            return Response({
                    "Error": "No vendor",
                    "Błąd": "Nie ma żadnego sprzedającego",
                    }, 
                    status=404
                )
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

            # for index, row in df.head(150).iterrows():  # Use .head(5) to get the first 5 rows
            for index, row in df.iterrows():
                # print('***PANDAS-ROW-SKU***', row[7])
                if row.iloc[7] == 'Aktywna':
                    # print('***PANDAS-ROW-SKU***', row.to_dict())

                    # print('***PANDAS-ROW-title***', row[21])
                    # print('***PANDAS-ROW-SKU***', row[11])
                    # print('***PANDAS-ROW-stock_qty***', row[12])
                    # print('***PANDAS-ROW-price***', row[14])

                    category = row.iloc[10].split('>')
                    # print('*** PANDAS-ROW-category ***', category)
                    for cat in category:
                        # clean_cat = re.sub(r"\s*\(\d+\)", "", category).strip()
                        match = re.search(r"\((\d+)\)", cat)
                        if match:
                            allegro_cat_id = match.group(1)

                    # print('*** PANDAS-ROW category MAIN ***', category[0])
                    cat_set.add(category[-1:][0])
                    # print('*** PANDAS-ROW clean_cat ***', clean_cat)
                    # print('*** PANDAS-ROW allegro_cat_id ***', allegro_cat_id)

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

                    #     print('***PANDAS-ROW***IMAGE --- STRIPT --- ', link.strip())
                    # print('***PANDAS-ROW***IMAGE --- LINKS ---', img_links)
                    # print('----------------------------------------------',)
                    # print('##############################################',)
                    # print('----------------------------------------------',)

                    sub_cat = []
                    try:
                        category_ = Category.objects.get(
                            title=re.sub(r"\s*\(\d+\)", "", category[0]).strip(),
                            )
                        for cat in category[1:]:
                            category_.category_hierarchy.append(cat),
                        category_.allegro_cat_id=allegro_cat_id
                        category_.save()
                    except:
                        category_, created = Category.objects.get_or_create(
                            title=re.sub(r"\s*\(\d+\)", "", category[0]).strip(),
                            category_hierarchy=[],
                            allegro_cat_id=allegro_cat_id
                        )  
                        for cat in category[1:]:
                            category_.category_hierarchy.append(cat),
                        category_.save()

                    product, created_product = Product.objects.get_or_create(
                        title=row.iloc[21],
                        # image = img_links[0].replace(',', ''),
                        img_links=img_links,
                        description=descr,
                        price=safe_decimal(row.iloc[14]),
                        stock_qty=row.iloc[12],
                        sku=row.iloc[11],
                        shipping_amount=safe_decimal(14.99),
                        category=category_,
                        sub_cat=category,
                    )
                    product.vendors.add(vendor)
                    product.save()

            categories = Category.objects.all()
            for cat in categories:
                cat_ = Category.objects.get(title=cat.title)
                cat_.category_hierarchy=list(set(cat_.category_hierarchy))
                cat_.save()

            return Response({"message": "CSV processed successfully"}, status=201)
        except Exception as e:
            # Log full error and traceback
            import traceback
            error_message = traceback.format_exc()
            print(f"Error: {error_message}")
            return Response({"error": str(e)}, status=500)
        


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



# import random
# import string

# def generate_pid(length=10):
#     alphabet = "abcdefghijklmnopqrstuvxyz"
#     return ''.join(random.choice(alphabet) for _ in range(length))


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
                            product.image.save(f"{product.sku}.jpeg", ContentFile(compressed_img.read()), save=True)
                            product.thumbnail.save(f"{product.sku}.webp", ContentFile(compressed_img.read()), save=True)
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






# async def fetch_image(client, url: str) -> Image.Image | None:
#     try:
#         resp = await client.get(url, timeout=10)
#         resp.raise_for_status()
#         img = Image.open(BytesIO(resp.content))
#         return img.convert("RGB")
#     except Exception as e:
#         print("Failed to fetch", url, e)
#         return None

# async def fetch_all(urls: list[str]) -> list[Image.Image]:
#     async with httpx.AsyncClient() as client:
#         tasks = [fetch_image(client, u) for u in urls]
#         return await asyncio.gather(*tasks)
    
# def compress_image(img: Image.Image, max_size_kb=200) -> BytesIO:
#     output = BytesIO()
#     quality = 85
#     while True:
#         output.seek(0)
#         output.truncate()
#         img.save(output, format="JPEG", quality=quality, optimize=True)
#         if output.tell() <= max_size_kb * 1024 or quality <= 10:
#             break
#         quality -= 5
#     output.seek(0)
#     return output


# def save_product_images(product, images: list[Image.Image]): 
#     for idx, img in enumerate(images):
#     # for idx, img in enumerate(images):
#         if not img:
#             continue
#         compressed = compress_image(img)
#         if idx == 0:
#             product.thumbnail.save(
#                 f"{product.sku}_thumb.jpg",
#                 ContentFile(compressed.read()),
#                 save=True
#             )
#         else:
#             gallery = Gallery(product=product)
#             gallery.image.save(
#                 f"{product.sku}_{idx}.jpg",
#                 ContentFile(compressed.read()),
#                 save=True
#             )






# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from asgiref.sync import sync_to_async


# class LinksToGallery(APIView):
#     permission_classes = (AllowAny,)

#     async def post(self, request):
#         try:
#             # ORM call wrapped in sync_to_async
#             products = await sync_to_async(list)(Product.objects.all())

#             for product in products:
#                 if not product.img_links:
#                     continue

#                 # async httpx fetch
#                 images = await fetch_all(product.img_links)

#                 # save_product_images is sync (uses ORM + file I/O)
#                 await sync_to_async(save_product_images)(product, images)

#             return Response({"message": "Images stored successfully"})
#         except Exception as e:
#             return Response({"message": f"Error: {e}"})



# class ContactView(APIView):

#     permission_classes = (AllowAny, )

#     def post(self, request, *args, **kwargs):
#         full_name = request.data['full_name']
#         email = request.data['email']
#         subject = request.data['subject']
#         message = request.data['message']

#         contact = Contact(
#             full_name=full_name,
#             email=email,
#             subject=subject,
#             message=message,
#         )
#         contact.save()

#         return Response({
#             "message": "Your message has been sent. We will contact you soon!"
#         })




class ResizeImageView(APIView):
    def get(self, request):
        image_url = request.query_params.get('url')
        width = int(request.query_params.get('w', 200))
        height = int(request.query_params.get('h', 200))

        # print('********** ResizeImageView **********', image_url, width, height)

        if not image_url:
            return Response({'error': 'Missing image URL'}, status=400)

        product = Product.objects.filter(img_links__contains=[image_url]).first()
        if not product:
            return Response({'error': 'Product not found'}, status=404)

        generate_thumbnail.delay(product.id, image_url, width, height)
        # test.delay(2, 2)

        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content)).convert('RGB')
        img.thumbnail((width, height), Image.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=80)
        buffer.seek(0)

        return HttpResponse(buffer.getvalue(), content_type="image/webp")
        # return Response({'status': 'Thumbnail task queued'}, status=202)
    


from .models import AllegroBatch, SeoTitleBatch

def batch_status_view(request, batch_id):
    batch = get_object_or_404(AllegroBatch, id=batch_id)
    return render(request, "admin/store/batch_status.html", {"batch": batch})



def update_batch_status_view(request, batch_id):
    batch = get_object_or_404(AllegroProductBatch, id=batch_id)
    logs = batch.logs.select_related("product").order_by("id")

    # 🔥 ZBIERAMY WSZYSTKIE SKU Z LOGÓW
    all_skus = ",".join([log.product.sku for log in logs])

    # for log in logs:
    #     print('***** LOG SKU *****', log.product.sku)
    #     print('***** LOG MESSAGE *****', log.message)

    return render(
        request,
        "admin/store/update_products_status_.html",
        {
            "batch": batch,
            "logs": logs,
            "all_skus": all_skus,
        }
    )



def seo_title_batch_status(request, batch_id):
    batch = get_object_or_404(SeoTitleBatch, id=batch_id)
    logs = batch.logs.select_related("product").order_by("id")

    # 🔥 ZBIERAMY WSZYSTKIE SKU Z LOGÓW
    all_skus = ",".join([log.product.sku for log in logs])
    
    return render(request, "admin/store/seo_title_batch_status_.html", {
        "batch": batch,
        "logs": logs,
        "all_skus": all_skus,
    })


class FrontendBatchStatusView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, batch_id):
        batch = get_object_or_404(AllegroProductBatch, id=batch_id)
        logs = batch.logs.select_related("product").order_by("id")

        # 🔥 ZBIERAMY WSZYSTKIE SKU Z LOGÓW
        all_skus = ",".join([log.product.sku for log in logs])
        return Response({
            # "status": batch.status,
            # "progress": batch.progress,
            # "total_products": batch.total_products,
            # "finished_at": batch.finished_at
            "batch": batch,
            "logs": logs,
            "all_skus": all_skus,
        })
