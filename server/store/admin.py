from django.contrib import admin
from django import forms

from import_export.admin import ImportExportModelAdmin

from store.models import *

class GalleryInline(admin.TabularInline):
    model = Gallery

class SpecificationInline(admin.TabularInline):
    model = Specification

class SizeInline(admin.TabularInline):
    model = Size

class ColorInline(admin.TabularInline):
    model = Color

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    vendor = forms.ModelChoiceField(queryset=Vendor.objects.filter(user__is_staff=True))

class ProductAdmin(ImportExportModelAdmin):
    # inlines = [ProductImagesAdmin, SpecificationAdmin, ColorAdmin, SizeAdmin]
    search_fields = ['title', 'price', 'slug']
    list_filter = ['featured', 'status', 'in_stock', 'type', 'vendor']
    list_editable = ['image', 'title', 'price', 'featured', 'status',  'shipping_amount', 'hot_deal', 'special_offer']
    list_display = ['product_image', 'image', 'title',   'price', 'featured', 'shipping_amount', 'in_stock' ,'stock_qty',  'vendor' ,'status', 'featured', 'special_offer' ,'hot_deal']
    # actions = [make_published, make_in_review, make_featured]
    inlines = [GalleryInline, SpecificationInline, SizeInline, ColorInline]
    list_per_page = 100
    prepopulated_fields = {"slug": ("title", )}
    form = ProductAdminForm

admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(Gallery)
admin.site.register(Cart)
admin.site.register(CartOrder)
admin.site.register(CartOrderItem)
