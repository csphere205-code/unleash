from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .models import (
    Product, Color, Category, Combo, Offer, OfferCampaign,
    StoreLocation, Cart, CartItem, ProductImage, HeroSlide, Order, OrderItem
)


# ============================================
# DELIVERY FEE CONFIGURATION
# ============================================

DELIVERY_FEES = {
    'Nairobi': 300,
    'Nakuru': 400,
    'Mombasa': 500,
    'Meru': 450,
    'Other': 600,
}


def get_delivery_fee(city):
    """Returns the delivery fee for a given city."""
    return DELIVERY_FEES.get(city, DELIVERY_FEES['Other'])


# ============================================
# CART HELPERS
# ============================================

def get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            return Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            pass
    cart = Cart.objects.create()
    request.session['cart_id'] = cart.id
    return cart


# ============================================
# STOREFRONT VIEWS
# ============================================

def home(request):
    colors = Color.objects.all()
    bestsellers = Product.objects.filter(is_bestseller=True)[:4]
    combos = Combo.objects.filter(is_active=True)[:4]
    cart = get_or_create_cart(request)
    hero_slides = HeroSlide.objects.filter(is_active=True)
    
    all_campaigns = OfferCampaign.objects.filter(is_active=True)
    live_campaigns = [c for c in all_campaigns if c.is_live][:2]
    
    return render(request, 'store/home.html', {
        'colors': colors,
        'bestsellers': bestsellers,
        'combos': combos,
        'cart': cart,
        'hero_slides': hero_slides,
        'active_campaigns': live_campaigns,
    })


def shop_view(request, category_slug=None):
    products = Product.objects.all()
    category = None
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    cart = get_or_create_cart(request)
    return render(request, 'store/shop.html', {
        'products': products,
        'category': category,
        'cart': cart,
    })


def search_view(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    else:
        products = Product.objects.none()
    
    cart = get_or_create_cart(request)
    return render(request, 'store/search.html', {
        'query': query,
        'products': products,
        'cart': cart,
    })


# ============================================
# PRODUCT DETAIL
# ============================================

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    available_images = ProductImage.objects.filter(product=product).select_related('color')
    
    offer = None
    product_offers = Offer.objects.filter(product=product, is_active=True)
    for o in product_offers:
        if not o.campaign or o.campaign.is_live:
            offer = o
            break

    cart = get_or_create_cart(request)
    return render(request, 'store/product_detail.html', {
        'product': product,
        'available_images': available_images,
        'offer': offer,
        'cart': cart,
    })


# ============================================
# COMBOS
# ============================================

def combo_list(request):
    combos = Combo.objects.filter(is_active=True)
    cart = get_or_create_cart(request)
    return render(request, 'store/combos.html', {
        'combos': combos,
        'cart': cart,
    })


# ============================================
# OFFER CAMPAIGNS
# ============================================

def offer_campaign_list(request):
    all_campaigns = OfferCampaign.objects.filter(is_active=True)
    live_campaigns = [c for c in all_campaigns if c.is_live]
    
    cart = get_or_create_cart(request)
    return render(request, 'store/offer_campaigns.html', {
        'campaigns': live_campaigns,
        'cart': cart,
    })


def offer_campaign_detail(request, slug):
    campaign = get_object_or_404(OfferCampaign, slug=slug)
    
    if not campaign.is_live:
        return redirect('offer_list')
        
    offers = campaign.offers.filter(is_active=True)
    cart = get_or_create_cart(request)
    return render(request, 'store/offer_campaign_detail.html', {
        'campaign': campaign,
        'offers': offers,
        'cart': cart,
    })


# ============================================
# CART ACTIONS
# ============================================

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    color_id = request.POST.get('color_id')
    color = get_object_or_404(Color, id=color_id) if color_id else None
    
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, color=color)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def add_combo_to_cart(request, combo_id):
    """Adds a combo bundle to the cart as a single line item."""
    combo = get_object_or_404(Combo, id=combo_id, is_active=True)
    cart = get_or_create_cart(request)
    
    item, created = CartItem.objects.get_or_create(cart=cart, combo=combo)
    if not created:
        item.quantity += 1
    item.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def update_cart_quantity(request, item_id, action):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    
    cart.refresh_from_db()
    total_items = cart.items.count()
    total_price = cart.total_price

    return JsonResponse({
        'success': True,
        'item_id': item_id,
        'action': action,
        'total_items': total_items,
        'total_price': float(total_price),
    })


def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ============================================
# CHECKOUT & ORDERS
# ============================================

def checkout(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    if not cart_items:
        return redirect('home')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        delivery_address = request.POST.get('delivery_address')
        
        # Calculate delivery fee based on selected city
        delivery_fee = get_delivery_fee(city)
        
        with transaction.atomic():
            order = Order.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                city=city,
                delivery_address=delivery_address,
                delivery_fee=delivery_fee,
                total_amount=0,
                status='pending',
            )
            
            for item in cart_items:
                if item.combo:
                    first_product = item.combo.products.first()
                    if first_product:
                        OrderItem.objects.create(
                            order=order,
                            product=first_product,
                            quantity=item.quantity,
                            price_at_purchase=item.combo.combo_price,
                        )
                    continue
                
                # Individual product logic (with best offer)
                final_price = item.product.price
                active_offer = None
                for candidate in item.product.offers.filter(is_active=True):
                    if candidate.campaign and not candidate.campaign.is_live:
                        continue
                    if active_offer is None or candidate.discount_price < final_price:
                        final_price = candidate.discount_price
                        active_offer = candidate
                
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    color=item.color,
                    quantity=item.quantity,
                    price_at_purchase=final_price,
                )
            
            # Total = items subtotal + delivery fee
            items_subtotal = sum(item.subtotal for item in order.items.all())
            order.total_amount = items_subtotal + delivery_fee
            order.save()
            
            cart_items.delete()
        
        return redirect('order_success', order_id=order.id)
    
    return render(request, 'store/checkout.html', {
        'cart': cart,
        'cart_items': cart_items,
        'delivery_fees': DELIVERY_FEES,
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_success.html', {
        'order': order,
    })