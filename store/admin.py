from django.contrib import admin
from django.utils import timezone
from .models import (
    SiteSetting, Color, Category, Product, ProductImage, 
    Combo, Offer, OfferCampaign, StoreLocation, Cart, CartItem, HeroSlide, Order, OrderItem
)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('top_banner_text', 'primary_green', 'page_background')


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_bestseller')
    list_editable = ('is_bestseller',)
    list_filter = ('category',)
    inlines = [ProductImageInline]


@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ('title', 'combo_price', 'savings', 'is_active')


class OfferInline(admin.TabularInline):
    model = Offer
    extra = 3
    fields = ('product', 'discount_price', 'is_active')


@admin.register(OfferCampaign)
class OfferCampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_live_status', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [OfferInline]
    list_filter = ('is_active', 'start_date', 'end_date')
    
    # Single, correct fields definition
    fields = ('title', 'slug', 'description', 'banner_image', 'start_date', 'end_date', 'is_active')

    def is_live_status(self, obj):
        if obj.is_live:
            return "🟢 Live Now"
        elif obj.end_date and timezone.now() > obj.end_date:
            return "🔴 Expired"
        elif obj.start_date and timezone.now() < obj.start_date:
            return "🟡 Scheduled"
        else:
            return "⚪ Inactive"
    is_live_status.short_description = 'Status'


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'discount_price', 'savings', 'is_active')
    list_filter = ('campaign', 'is_active')


@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ('city', 'phone')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'is_active', 'button_link')
    list_editable = ('order', 'is_active')
    fields = ('image', 'button_link', 'is_active', 'order')
    
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'color', 'quantity', 'price_at_purchase')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'city', 'delivery_fee', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'city', 'created_at')
    search_fields = ('full_name', 'phone', 'email')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'paid_at', 'delivery_fee')