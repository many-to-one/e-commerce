from django.shortcuts import render
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import CartCheckSerializer, ProductSerializer, CategorySerializer, GallerySerializer, CartSerializer
from .models import Category, Product, Cart, User, CartOrder

from decimal import Decimal


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

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
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

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
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
        product_id = request.data['product_id']
        quantity = request.data['quantity']
        product = Product.objects.get(id=product_id)
        user = User.objects.get(id=user_id)
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

        user_id = id #request.data['user_id']
        cart = Cart.objects.filter(user__id=user_id)
        for c in cart:
            print('CartView ------', c)
        cart_serializer = CartSerializer(cart, many=True)

        return Response({
            "cart": cart_serializer.data,
        })