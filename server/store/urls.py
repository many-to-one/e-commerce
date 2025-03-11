from django.urls import path
from .views import *

urlpatterns = [
    path('categories', CategoriesView.as_view(), name='categories'),
    path('products', ProductsView.as_view(), name='products'),
    path('product/<int:id>', ProductDetailsView.as_view(), name='product-details'),
    path('category-products/<int:id>', ProductsByCat.as_view(), name='category-products'),
    path('add-to-cart', AddToCardView.as_view(), name='add-to-cart'),
    path('cart/<int:id>', CartView.as_view(), name='cart'),
    path('cart_count/<int:id>', CartCountView.as_view(), name='cacart_countrt'),
    path('create-order', CreateOrderView.as_view(), name='create-order'),
    path('order-history', CartOrderItemView.as_view(), name='order-history'),
    path('couriers', DeliveryCouriersView.as_view(), name='couriers'),
    path('stripe-payment', StripeView.as_view(), name='stripe-payment'),
    path('finish-order', FinishedCartOrderView.as_view(), name='finish-order'),
    path('upload-csv', ProductCSVView.as_view(), name='upload-csv'),
    path('delete-all-products', DeleteProductsView.as_view(), name='delete-all-products'),
    path('convert-links-to-imgs', LinksToGallery.as_view(), name='convert-links-to-imgs'),
]