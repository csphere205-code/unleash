from django.db import models
from django.utils.text import slugify
from django.utils import timezone


# ============================================
# GLOBAL SETTINGS
# ============================================

class SiteSetting(models.Model):
    page_background = models.CharField(max_length=7, default='#F8F2EB')
    text_ink = models.CharField(max_length=7, default='#1B150F')
    card_panel = models.CharField(max_length=7, default='#FDF9F4')
    primary_green = models.CharField(max_length=7, default='#425430')
    soft_sand = models.CharField(max_length=7, default='#EBE3DA')
    muted_text = models.CharField(max_length=7, default='#665B53')
    warm_brown = models.CharField(max_length=7, default='#865634')
    borders = models.CharField(max_length=7, default='#D8CFC7')
    top_banner_text = models.CharField(max_length=200, default="COMBO DEALS ON NOW · NAIROBI · NAKURU · MERU · MOMBASA")

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Global Site Settings"


# ============================================
# CATALOG
# ============================================

class Color(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, help_text="e.g., #4A3B32")
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    is_bestseller = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_available_colors(self):
        return Color.objects.filter(product_images__product=self).distinct()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='products/')

    class Meta:
        unique_together = ('product', 'color')

    def __str__(self):
        return f"{self.product.name} - {self.color.name}"


# ============================================
# PROMOTIONS
# ============================================

class Combo(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    combo_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='combos/')
    products = models.ManyToManyField(Product, related_name='combos')
    is_active = models.BooleanField(default=True)

    @property
    def savings(self):
        return self.original_price - self.combo_price

    def __str__(self):
        return self.title


class OfferCampaign(models.Model):
    """A collection of offers, e.g., 'Mashujaa Day Sale' or 'Black November'."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Short description for the homepage section.")
    banner_image = models.ImageField(upload_to='campaigns/', blank=True, null=True, help_text="Optional banner for the campaign page.")
    
    start_date = models.DateTimeField(default=timezone.now, help_text="When does this campaign start?")
    end_date = models.DateTimeField(null=True, blank=True, help_text="When does this campaign end? Leave blank for no end date.")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Offer Campaign"
        verbose_name_plural = "Offer Campaigns"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_live(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    @property
    def time_remaining_seconds(self):
        """Returns the number of seconds left until the campaign ends."""
        if not self.end_date:
            return 0
        now = timezone.now()
        if self.end_date > now:
            return int((self.end_date - now).total_seconds())
        return 0


class Offer(models.Model):
    """A specific discount on a product within a campaign."""
    campaign = models.ForeignKey(
        OfferCampaign, 
        on_delete=models.CASCADE, 
        related_name='offers',
        null=True, 
        blank=True,
        help_text="Which campaign does this offer belong to?"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    @property
    def savings(self):
        return self.product.price - self.discount_price

    @property
    def title(self):
        return f"{self.product.name} - {self.campaign.title if self.campaign else 'Standalone'}"

    def __str__(self):
        return self.title


# ============================================
# MARKETING
# ============================================

class HeroSlide(models.Model):
    image = models.ImageField(upload_to='hero/', help_text="Upload the 16:9 landscape campaign banner here.")
    button_link = models.CharField(
        max_length=200, 
        default="/", 
        help_text="Where should this banner click to? (e.g., /combos/, /category/travel-bags/, or /offers/)"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of appearance (0 = first)")

    class Meta:
        ordering = ['order']
        verbose_name = "Hero Banner"
        verbose_name_plural = "Hero Banners"

    def __str__(self):
        return f"Banner {self.order} - {'Active' if self.is_active else 'Inactive'}"


class StoreLocation(models.Model):
    city = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.city


# ============================================
# CART
# ============================================

class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Cart {self.id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE, null=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def item_price(self):
        """Returns the effective price of this cart item."""
        if self.combo:
            return self.combo.combo_price
        return self.product.price

    @property
    def total_price(self):
        return self.item_price * self.quantity

    def __str__(self):
        name = self.combo.title if self.combo else self.product.name
        return f"{self.quantity} x {name}"


# ============================================
# ORDERS
# ============================================

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    delivery_address = models.TextField()
    
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"

    @property
    def subtotal(self):
        """Sum of order items (excludes delivery fee)."""
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    """A single item inside an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}"