from django.urls import path
from .views import *

urlpatterns = [
    path('products', ProductsView.as_view(), name='products'),
    path('categories', CategoriesView.as_view(), name='categories'),
]