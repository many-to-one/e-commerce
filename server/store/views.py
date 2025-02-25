from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework import generics, status
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import CartCheckSerializer, ProductSerializer, CategorySerializer, GallerySerializer, CartSerializer, DeliveryCouriersSerializer, CartOrderSerializer
from .models import Category, Product, Cart, User, CartOrder, DeliveryCouriers

from decimal import Decimal
import stripe

stripe.api_key = "sk_test_51LcCvDA045wcSZH2LYObmRvhCHdcnzTqZwz0jl9XNSAleSX5vCqeWeKGFiTY9NaMHiQEqRVSkbSKqwPBpwqraGW000VyX8ddrp"

class CategoriesView(generics.ListAPIView):

    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = (AllowAny, )


class ProductsView(generics.ListAPIView):

    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = (AllowAny, )


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
        )
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

                success_url=settings.SITE_URL+'/payment-success/'+ order.oid +'?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_URL+'/?session_id={CHECKOUT_SESSION_ID}',
            )
            order.stripe_session_id = checkout_session.id 
            order.save()

            # return redirect(checkout_session.url)
            return Response({
                "checkout_session": checkout_session.url
            })
        except stripe.error.StripeError as e:
            return Response( {'error': f'Something went wrong when creating stripe checkout session: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class FinishedCartOrderView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        oid = request.data["oid"]
        order = CartOrder.objects.get(oid=oid)
        order.payment_status = "paid"
        order.order_status = "Fulfilled"
        order.save()

        return Response({
            "message": "ok",
        })