import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon_name = models.CharField(max_length=50, default='bi-tag', help_text="Bootstrap icon name or emoji")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=10)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    image_url = models.URLField(blank=True, null=True, help_text="Direct image URL if not uploading file")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.discount_price < self.price:
            diff = self.price - self.discount_price
            return int((diff / self.price) * 100)
        return 0

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=60'

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart #{self.id} ({self.user.username if self.user else 'Guest - ' + str(self.session_key)})"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    @property
    def subtotal(self):
        return self.product.effective_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Order Placed (Pending)'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card (Mock)'),
        ('upi', 'UPI / Online (Mock)'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    
    # Shipping details
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Payment & Totals
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Order Tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    tracking_number = models.CharField(max_length=60, blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = 'ORD-' + uuid.uuid4().hex[:10].upper()
        if not self.tracking_number and self.status in ['Shipped', 'Delivered']:
            self.tracking_number = 'TRK-' + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    @property
    def status_step(self):
        """Returns step index for visual timeline: 1 to 4 (or -1 if Cancelled)"""
        mapping = {
            'Pending': 1,
            'Processing': 2,
            'Shipped': 3,
            'Delivered': 4,
            'Cancelled': -1,
        }
        return mapping.get(self.status, 1)

    def __str__(self):
        return f"{self.order_number} - {self.user.username} (${self.total_amount})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Order: {self.order.order_number})"
