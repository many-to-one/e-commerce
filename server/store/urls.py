from django.urls import path
from .views import *
from .allegro_views.views import exchange_token_view, AllegroOrderAdminView, ProductAdminView, EditProductAdminView
from .allegro_views.vendors import *

urlpatterns = [
    path('categories', CategoriesView.as_view(), name='categories'),
    path('products', ProductsView.as_view(), name='products'),
    path('popular', PopularProductsView.as_view(), name='popular'),
    path('discounts', DiscountProductsView.as_view(), name='discounts'),
    path('news', NewsProductsView.as_view(), name='news'),
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
    path('upload-presta-csv', PrestaCSVView.as_view(), name='upload-presta-csv'), 
    path('update-presta-csv', PrestaUpdateCSVView.as_view(), name='update-presta-csv'), 
    path('delete-all-products', DeleteProductsView.as_view(), name='delete-all-products'),
    path('convert-links-to-imgs', LinksToGallery.as_view(), name='convert-links-to-imgs'),
    path('resize', ResizeImageView.as_view(), name='resize'),

    path('allegro-token/<str:code>/<str:vendor_name>/', exchange_token_view, name='allegro-token'),
    path('vendors/<str:email>', user_vendors, name='vendors'),

    path('admin/sync-allegro-orders/', AllegroOrderAdminView.as_view(), name='sync_allegro_orders'), 
    # path('admin/create-allegro-orders/', AllegroCreateOrderView.as_view(), name='create_allegro_orders'),
    path('admin/sync-allegro-offers/', ProductAdminView.as_view(), name='sync_allegro_offers'),
    path('admin/edit-allegro-offers/', EditProductAdminView.as_view(), name='edit_allegro_offers'),
    path("admin/allegrobatch/<int:batch_id>/status/", batch_status_view, name="allegro_batch_status"),
    path("admin/allegroupdatebatch/<int:batch_id>/status/", update_batch_status_view, name="allegroupdatebatch_status"),
    path("admin/seotitlebatch/<int:batch_id>/status/", seo_title_batch_status, name="seo_title_batch_status"),

    path('vendor-contact', VendorContact.as_view(), name='vendor-contact'),
]