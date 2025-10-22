import csv
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from store.models import *
# from addon.models import ConfigSettings
from store.models import Gallery
from users.serializer import ProfileSerializer, UserSerializer


# Define a serializer for the Category model
class CategorySerializer(serializers.ModelSerializer):
    category_hierarchy = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    def get_category_hierarchy(self, obj):
        # Skip the first element and clean the remaining elements
        if obj.category_hierarchy:
            cleaned_hierarchy = [
                item.split('(')[0].strip() for item in obj.category_hierarchy #[1:]
            ]
            return cleaned_hierarchy
        return []

# Define a serializer for the Tag model
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

# Define a serializer for the Brand model
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'


# Define a serializer for the Gallery model
class GallerySerializer(serializers.ModelSerializer):
    # Serialize the related Product model

    class Meta:
        model = Gallery
        fields = '__all__'

# Define a serializer for the Specification model
class SpecificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Specification
        fields = '__all__'

# Define a serializer for the Size model
class SizeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Size
        fields = '__all__'

# Define a serializer for the Color model
class ColorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Color
        fields = '__all__'


class IconProductSerializer(serializers.ModelSerializer):

    gallery = GallerySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "image",
            "img_links",
            "slug",
            "category",
            "gallery",
            "price",
            "old_price",
            "hot_deal",
            "product_rating",
        ]


# Define a serializer for the Product model
class ProductSerializer(serializers.ModelSerializer):
    # Serialize related Category, Tag, and Brand models
    # category = CategorySerializer(many=True, read_only=True)
    # tags = TagSerializer(many=True, read_only=True)
    gallery = GallerySerializer(many=True, read_only=True)
    color = ColorSerializer(many=True, read_only=True)
    size = SizeSerializer(many=True, read_only=True)
    specification = SpecificationSerializer(many=True, read_only=True)
    # rating = serializers.IntegerField(required=False)
    
    # specification = SpecificationSerializer(many=True, required=False)
    # color = ColorSerializer(many=True, required=False)
    # size = SizeSerializer(many=True, required=False)
    # gallery = GallerySerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "image",
            "img_links",
            "description",
            "category",
            "sub_cat",
            "tags",
            "brand",
            "price",
            "old_price",
            "shipping_amount",
            "stock_qty",
            "in_stock",
            "status",
            "type",
            "featured",
            "hot_deal",
            "special_offer",
            "digital",
            "views",
            "orders",
            "saved",
            # "rating",
            "vendors",
            "sku",
            "pid",
            "slug",
            "date",
            "gallery",
            "specification",
            "size",
            "color",
            "product_rating",
            "rating_count",
            # 'order_count',
            "get_precentage",
        ]


# Define a serializer for the ProductFaq model
class ProductFaqSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    product = ProductSerializer()

    class Meta:
        model = ProductFaq
        fields = '__all__'


# Define a serializer for the CartOrderItem model
class CartSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    product = ProductSerializer()  

    class Meta:
        model = Cart
        fields = '__all__'



class CartCheckSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    user_id = serializers.CharField(
        write_only=True,
        required=True,
    ) 

    class Meta:
        model = Cart
        fields = '__all__'
    

# Define a serializer for the CartOrderItem model
class CartOrderItemSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    # order = CartOrderSerializer()
    product = ProductSerializer()  

    class Meta:
        model = CartOrderItem
        fields = '__all__'
    


# Define a serializer for the CartOrder model
class CartOrderSerializer(serializers.ModelSerializer):
    # Serialize related CartOrderItem models
    orderitem = CartOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = CartOrder
        fields = '__all__'


class ReturnOrderItemSerializer(serializers.ModelSerializer):
    # Serialize the related ReturnItem model
    order = CartOrderSerializer()
    product = ProductSerializer()  

    class Meta:
        model = ReturnItem
        fields = '__all__'




class VendorSerializer(serializers.ModelSerializer):
    # Serialize related CartOrderItem models
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = '__all__'


# Define a serializer for the Review model
class ReviewSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    product = ProductSerializer()
    profile = ProfileSerializer()
    
    class Meta:
        model = Review
        fields = '__all__'


# Define a serializer for the Wishlist model
class WishlistSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    product = ProductSerializer()

    class Meta:
        model = Wishlist
        fields = '__all__'


# Define a serializer for the Address model
class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = '__all__'


# Define a serializer for the CancelledOrder model
class CancelledOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = CancelledOrder
        fields = '__all__'


# Define a serializer for the Coupon model
class CouponSerializer(serializers.ModelSerializer):

    class Meta:
        model = Coupon
        fields = '__all__'


# # Define a serializer for the CouponUsers model
# class CouponUsersSerializer(serializers.ModelSerializer):
#     # Serialize the related Coupon model
#     coupon =  CouponSerializer()

#     class Meta:
#         model = CouponUsers
#         fields = '__all__'


# Define a serializer for the DeliveryCouriers model
class DeliveryCouriersSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryCouriers
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = '__all__'


class SummarySerializer(serializers.Serializer):
    products = serializers.IntegerField()
    orders = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)

class EarningSummarySerializer(serializers.Serializer):
    monthly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)


class CouponSummarySerializer(serializers.Serializer):
    total_coupons = serializers.IntegerField(default=0)
    active_coupons = serializers.IntegerField(default=0)


class NotificationSummarySerializer(serializers.Serializer):
    un_read_noti = serializers.IntegerField(default=0)
    read_noti = serializers.IntegerField(default=0)
    all_noti = serializers.IntegerField(default=0)


class StripePaymentSerializer(serializers.Serializer):
    amount = serializers.IntegerField()  # Amount in cents
    currency = serializers.CharField(max_length=3, default="usd")


class ProductCSVSerializer(serializers.Serializer):
    csv_file = serializers.FileField()

    def create(self, validated_data):
        csv_file = validated_data['csv_file']
        print('ProductCSVSerializer', csv_file)
        return csv_file

        # # Read the CSV file
        # decoded_file = csv_file.read().decode('utf-8').splitlines()
        # reader = csv.DictReader(decoded_file)

        # created_products = []
        # for row in reader:
        #     print()
        #     uuid_key = shortuuid.uuid()
        #     uniqueid = uuid_key[:4]
        #     slug = f"{row['title'].lower().replace(' ', '-')}-{uniqueid}"

        #     product, created = Product.objects.get_or_create(
        #         sku=row['sku'],
        #         defaults={
        #             'title': row['title'],
        #             'description': row.get('description', ''),
        #             'price': float(row['price']),
        #             'stock_qty': int(row['stock_qty']),
        #             'in_stock': int(row['stock_qty']) > 0,
        #             'slug': slug
        #         }
        #     )
        #     if created:
        #         created_products.append(product)

        # return {'created_count': len(created_products)}