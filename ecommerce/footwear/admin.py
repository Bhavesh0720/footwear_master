from django.contrib import admin
from .models import *


# Register your models here.
class ProductStockInLine(admin.TabularInline):
    model = ProductStock
    extra = 1


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    inlines = [ProductStockInLine]
    filter_horizontal = ('colors',)


admin.site.register(User)
admin.site.register(Main_Categories)
admin.site.register(Sub_Categories)
admin.site.register(ProductImages)
admin.site.register(Size)
admin.site.register(Width)
admin.site.register(Brand)
admin.site.register(Colors)
admin.site.register(Cart)
admin.site.register(Wishlist)
admin.site.register(Coupons)
admin.site.register(Applied_coupons)
admin.site.register(Adresses)
admin.site.register(Orders)
admin.site.register(OrderItem)
admin.site.register(Contacts)
admin.site.register(Review)

