from django.db import models
from django.utils.text import slugify
from django.conf import settings  # For AUTH_USER_MODEL reference
from django.core.exceptions import ValidationError

# ✅ Category Model
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    banner = models.ImageField(upload_to='gallery/categories/banners/', blank=True, null=True)  # ✅ New field
    mobile_banner = models.ImageField(upload_to='gallery/categories/banners/mobile/', blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product_list') + '?category=' + self.slug

    def get_min_price(self):
        # Get the minimum price of active products in this category
        min_price = self.product_set.filter(is_active=True).aggregate(models.Min('price'))['price__min']
        return min_price if min_price is not None else 0



# ✅ Product Model
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    min_wholesale_quantity = models.PositiveIntegerField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    
    def product_main_image_upload_path(instance, filename):
        return f'gallery/productimages/{instance.id}/main_{filename}'    
    image = models.ImageField(upload_to=product_main_image_upload_path, blank=True, null=True)
    
    def product_gif_upload_path(instance, filename):
        return f'gallery/productimages/{instance.id}/gif_{filename}'
    gif = models.ImageField(upload_to=product_gif_upload_path, blank=True, null=True, help_text="Animated GIF to show on hover")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product_detail', args=[str(self.slug)])

    def get_average_rating(self):
        from django.db.models import Avg
        avg_rating = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 1) if avg_rating else 0

    def get_review_count(self):
        return self.reviews.filter(is_approved=True).count()

    def get_rating_distribution(self):
        from django.db.models import Count
        distribution = self.reviews.filter(is_approved=True).values('rating').annotate(
            count=Count('rating')
        ).order_by('-rating')
        return {item['rating']: item['count'] for item in distribution}
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    
    def product_gallery_image_upload_path(instance, filename):
        return f'gallery/productimages/{instance.product.id}/{filename}'

    image = models.ImageField(upload_to=product_gallery_image_upload_path)

    def __str__(self):
        return f"{self.product.name} - Image"



# ✅ Cart Model
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Cart {self.id} for {self.user.username}"
        return f"Cart {self.id} for session {self.session_id}"

    def get_total(self):
        return sum(item.quantity * item.product.price for item in self.items.all())


# ✅ Cart Item Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    is_saved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


# ✅ Order Model
class Order(models.Model):
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online Payment'),
        ('cod', 'Cash on Delivery'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='online')
    cod_remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Amount to be paid on delivery for COD orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    seller_remark = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Order {self.id} by {self.user.username}"
        return f"Order {self.id} for {self.email}"



# ✅ Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"


# ✅ Wishlist Model
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"



from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=255, default="SmokeKing.in")
    logo = models.ImageField(upload_to='site_settings/logo/', blank=True, null=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ensure only one instance of SiteSettings exists
        if SiteSettings.objects.exists() and not self.pk:
            # if you'll not check for self.pk 
            # then error will also be raised in update of existing instance
            raise ValidationError('There can be only one SiteSettings instance')
        return super(SiteSettings, self).save(*args, **kwargs)

class BulkOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status_choices = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bulk Order for {self.product.name} by {self.full_name}"


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    review = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        if not self.pk:
            user_has_ordered = OrderItem.objects.filter(
                product=self.product,
                order__user=self.user,
                order__status__in=['paid', 'processing', 'shipped', 'delivered']
            ).exists()
            self.is_verified_purchase = user_has_ordered
        super().save(*args, **kwargs)


class ReviewHelpful(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')

    def __str__(self):
        helpful_text = "helpful" if self.is_helpful else "not helpful"
        return f"{self.user.username} found review {helpful_text}"