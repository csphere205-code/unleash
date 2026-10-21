from django.contrib import admin
from django.urls import path
from store import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    
    # Shop routes
    path('shop/', views.shop_view, name='shop'),
    path('shop/category/<slug:category_slug>/', views.shop_view, name='category_shop'),
    path('search/', views.search_view, name='search'),
    
    # Combos
    path('combos/', views.combo_list, name='combo_list'),
    
    # Offers
    path('offers/', views.offer_campaign_list, name='offer_list'),
    path('offers/<slug:slug>/', views.offer_campaign_detail, name='offer_campaign_detail'),
    
    # Products & Cart
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('add-combo-to-cart/<int:combo_id>/', views.add_combo_to_cart, name='add_combo_to_cart'),
    path('update-cart/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)