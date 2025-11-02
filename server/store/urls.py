from django.urls import path
from .views import *
from .allegro_views.views import exchange_token_view, AllegroOrderAdminView
from .allegro_views.vendors import *

urlpatterns = [
    path('categories', CategoriesView.as_view(), name='categories'),
    path('products', ProductsView.as_view(), name='products'),
    path('product/<int:id>', ProductDetailsView.as_view(), name='product-details'),
    path('category-products/<int:id>', ProductsByCat.as_view(), name='category-products'),
    path('sub-category-products/<str:sub_cat>', ProductsBySubCat.as_view(), name='sub-category-products'),
    path('add-to-cart', AddToCardView.as_view(), name='add-to-cart'),
    path('cart/<int:id>', CartView.as_view(), name='cart'),
    path('cart_count/<int:id>', CartCountView.as_view(), name='cacart_countrt'),
    path('create-order', CreateOrderView.as_view(), name='create-order'),
    path('return-item', ReturnProductView.as_view(), name='return-item'),
    path('returns', UsersReturns.as_view(), name='returns'),
    path('order-history', CartOrderItemView.as_view(), name='order-history'),
    path('couriers', DeliveryCouriersView.as_view(), name='couriers'),
    path('stripe-payment', PayUView.as_view(), name='stripe-payment'),
    path('finish-order', FinishedCartOrderView.as_view(), name='finish-order'),
    # path('upload-csv', TestView.as_view(), name='test'),
    path('upload-csv', ProductCSVView.as_view(), name='upload-csv'), 
    path('delete-all-products', DeleteProductsView.as_view(), name='delete-all-products'),
    path('convert-links-to-imgs', LinksToGallery.as_view(), name='convert-links-to-imgs'),

    path('allegro-token/<str:code>/<str:vendor_name>/', exchange_token_view, name='allegro-token'),
    path('vendors/<str:email>', user_vendors, name='vendors'),

    path('admin/sync-allegro-orders/', AllegroOrderAdminView.as_view(), name='sync_allegro_orders'),
    # path('admin/store/<int:invoice_id>/correction/', correction_view, name='correction_view'),
]