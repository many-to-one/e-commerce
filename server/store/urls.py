from django.urls import path
from .views import *

urlpatterns = [
    path('categories', CategoriesView.as_view(), name='categories'),
    path('products', ProductsView.as_view(), name='products'),
    path('product/<slug:slug>', ProductDetailsView.as_view(), name='product-details'),
]