from django.shortcuts import render
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import ProductSerializer, CategorySerializer, GallerySerializer
from .models import Category, Product


class CategoriesView(generics.ListAPIView):

    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = (AllowAny, )


class ProductsView(generics.ListAPIView):

    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = (AllowAny, )


class ProductDetailsView(APIView):

    permission_classes = (AllowAny, )

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        gallery = product.gallery()
        serializer = ProductSerializer(product)
        gallery_serializer = GallerySerializer(gallery, many=True)
        return Response({
            "product": serializer.data,
            "gallery": gallery_serializer.data,
        })