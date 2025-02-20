from django.urls import path
from .views import *

urlpatterns = [
    path('categories', CategoriesView.as_view(), name='categories'),
    path('products', ProductsView.as_view(), name='products'),
    path('product/<slug:slug>', ProductDetailsView.as_view(), name='product-details'),
    path('category-products/<slug:slug>', ProductsByCat.as_view(), name='category-products'),
    path('add-to-cart', AddToCardView.as_view(), name='add-to-cart'),
    path('cart/<int:id>', CartView.as_view(), name='cart'),
    path('cart_count/<int:id>', CartCountView.as_view(), name='cacart_countrt'),
    path('create-order', CreateOrderView.as_view(), name='create-order'),
    path('couriers', DeliveryCouriersView.as_view(), name='couriers'),
    path('stripe-payment', StripeView.as_view(), name='stripe-payment'),
    path('finish-order', FinishedCartOrderView.as_view(), name='finish-order'),
]