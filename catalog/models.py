from django.db import models
from django.conf import settings
import os
from django.utils.text import slugify


def category_image_path(instance, filename):
    """Generate upload path for category images"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.name)}.{ext}"
    return f"categories/{filename}"


def product_image_path(instance, filename):
    """Generate upload path for product images: products/images/{product_id}/{filename}"""
    ext = filename.split('.')[-1]
    # Clean filename and make it safe
    base_name = os.path.splitext(filename)[0]
    safe_filename = f"{slugify(base_name)}.{ext}"

    # If product doesn't have ID yet (creating new), use temporary folder
    if instance.pk:
        return f"products/images/{instance.pk}/{safe_filename}"
    else:
        return f"products/images/temp/{safe_filename}"


def product_gallery_image_path(instance, filename):
    """Generate upload path for product gallery images: products/images/{product_id}/{filename}"""
    ext = filename.split('.')[-1]
    base_name = os.path.splitext(filename)[0]
    safe_filename = f"{slugify(base_name)}.{ext}"

    # If product doesn't have ID yet, use temp folder
    if instance.product.pk:
        return f"products/images/{instance.product.pk}/{safe_filename}"
    else:
        return f"products/images/temp/{safe_filename}"


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to=category_image_path, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def get_all_children(self):
        """Get all child categories recursively"""
        children = list(self.children.all())
        for child in self.children.all():
            children.extend(child.get_all_children())
        return children

class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Leave empty if no sale")
    description = models.TextField(blank=True, default="")
    short_description = models.CharField(max_length=300, blank=True, default="")
    image = models.ImageField(upload_to=product_image_path, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    manage_stock = models.BooleanField(default=True, help_text="Enable stock management for this product")
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    sku = models.CharField(max_length=100, blank=True, unique=True, null=True, help_text="Stock Keeping Unit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def get_price(self):
        """Return sale price if available, otherwise regular price"""
        if self.sale_price:
            return self.sale_price
        return self.price

    @property
    def is_on_sale(self):
        """Check if product is currently on sale"""
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def discount_percentage(self):
        """Calculate discount percentage if on sale"""
        if self.is_on_sale:
            return int(((self.price - self.sale_price) / self.price) * 100)
        return 0

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.manage_stock:
            return True
        return self.stock_quantity > 0

    def reduce_stock(self, quantity):
        """Reduce stock quantity (used when order is placed)"""
        if self.manage_stock and self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save()
            return True
        return False

    def get_related_products(self, limit=4):
        """Get related products from same category"""
        return Product.objects.filter(
            category=self.category,
            is_active=True
        ).exclude(id=self.id)[:limit]

    def get_average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0

    def get_review_count(self):
        """Get count of approved reviews"""
        return self.reviews.filter(is_approved=True).count()

    def get_all_images(self):
        """Get all product images including main image"""
        images = []
        if self.image:
            images.append({
                'image': self.image,
                'is_main': True,
                'alt_text': f"{self.title} - Main Image",
                'order': 0
            })

        # Add additional images from ProductImage model
        for img in self.additional_images.all().order_by('order'):
            images.append({
                'image': img.image,
                'is_main': False,
                'alt_text': img.alt_text or f"{self.title} - Image {img.order}",
                'order': img.order
            })

        return images

    @property
    def main_image(self):
        """Get the primary display image"""
        if self.image:
            return self.image

        # Fallback to first additional image
        first_additional = self.additional_images.first()
        if first_additional:
            return first_additional.image

        return None

    def save(self, *args, **kwargs):
        """Custom save method to handle image organization"""
        # Check if this is a new product (no pk) and has an image
        is_new_product = not self.pk
        old_image_path = None

        if is_new_product and self.image:
            # Store the temporary path
            old_image_path = self.image.name

        # Save the product first to get the ID
        super().save(*args, **kwargs)

        # If this was a new product with an image in temp folder, move it to the proper location
        if is_new_product and old_image_path and old_image_path.startswith('products/images/temp/'):
            self._move_temp_image_to_product_folder()

    def _move_temp_image_to_product_folder(self):
        """Move image from temp folder to product-specific folder"""
        if not self.image:
            return

        try:
            from django.core.files.storage import default_storage
            import shutil

            old_path = self.image.path
            old_name = self.image.name

            if 'temp/' in old_name:
                # Generate new path
                filename = os.path.basename(old_name)
                new_name = f"products/images/{self.pk}/{filename}"
                new_path = os.path.join(settings.MEDIA_ROOT, new_name)

                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(new_path), exist_ok=True)

                # Move the file
                if os.path.exists(old_path):
                    shutil.move(old_path, new_path)

                    # Update the image field
                    self.image.name = new_name
                    super().save(update_fields=['image'])

        except Exception as e:
            # Log error but don't break the save process
            print(f"Error moving product image: {e}")
            pass


class ProductImage(models.Model):
    """Additional product images for gallery"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to=product_gallery_image_path)
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"{self.product.title} - Image {self.order}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f"{self.product.title} - Image {self.order}"

        # Check if this is a new image and has a temp path
        is_new_image = not self.pk
        old_image_path = None

        if is_new_image and self.image:
            old_image_path = self.image.name

        super().save(*args, **kwargs)

        # Move temp image to proper location if needed
        if is_new_image and old_image_path and 'temp/' in old_image_path:
            self._move_temp_image_to_product_folder()

    def _move_temp_image_to_product_folder(self):
        """Move gallery image from temp folder to product-specific folder"""
        if not self.image:
            return

        try:
            import shutil

            old_path = self.image.path
            old_name = self.image.name

            if 'temp/' in old_name:
                # Generate new path
                filename = os.path.basename(old_name)
                new_name = f"products/images/{self.product.pk}/{filename}"
                new_path = os.path.join(settings.MEDIA_ROOT, new_name)

                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(new_path), exist_ok=True)

                # Move the file
                if os.path.exists(old_path):
                    shutil.move(old_path, new_path)

                    # Update the image field
                    self.image.name = new_name
                    super().save(update_fields=['image'])

        except Exception as e:
            print(f"Error moving gallery image: {e}")
            pass


class ProductVariant(models.Model):
    """Product variants for size, color, etc."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text="e.g., 'Size', 'Color'")
    value = models.CharField(max_length=100, help_text="e.g., 'Large', 'Red'")
    price_adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Additional cost for this variant"
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['product', 'name', 'value']
        ordering = ['name', 'value']
    
    def __str__(self):
        return f"{self.product.title} - {self.name}: {self.value}"
    
    @property
    def final_price(self):
        """Calculate final price with variant adjustment"""
        return self.product.get_price + self.price_adjustment

    @property
    def is_in_stock(self):
        """Check if variant is in stock"""
        return self.stock_quantity > 0

    def reduce_stock(self, quantity):
        """Reduce variant stock quantity (used when order is placed)"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save()
            return True
        return False

class ProductReview(models.Model):
    """Product reviews and ratings"""
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.rating}/5)"

class SiteSettings(models.Model):
    """Global site settings"""
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('INR', 'Indian Rupee (₹)'),
        ('JPY', 'Japanese Yen (¥)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('CHF', 'Swiss Franc (CHF)'),
        ('CNY', 'Chinese Yuan (¥)'),
        ('SEK', 'Swedish Krona (kr)'),
        ('NOK', 'Norwegian Krone (kr)'),
        ('DKK', 'Danish Krone (kr)'),
        ('PLN', 'Polish Złoty (zł)'),
        ('CZK', 'Czech Koruna (Kč)'),
        ('HUF', 'Hungarian Forint (Ft)'),
        ('RUB', 'Russian Ruble (₽)'),
    ]

    THEME_CHOICES = [
        ('default', 'Default Theme'),
        ('modern', 'Modern Theme'),
        ('glam', 'Glam Theme'),
        ('smoke', 'Smoke Theme'),
    ]

    CURRENCY_SYMBOLS = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'INR': '₹',
        'JPY': '¥',
        'CAD': 'C$',
        'AUD': 'A$',
        'CHF': 'CHF',
        'CNY': '¥',
        'SEK': 'kr',
        'NOK': 'kr',
        'DKK': 'kr',
        'PLN': 'zł',
        'CZK': 'Kč',
        'HUF': 'Ft',
        'RUB': '₽',
    }

    # General Site Settings
    site_name = models.CharField(
        max_length=100,
        default='Ecom_CMS',
        help_text="Name of your website"
    )
    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default='glam',
        help_text="Visual theme for your website"
    )

    # Currency Settings
    default_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='INR',
        help_text="Default currency for the site"
    )

    # Review Settings
    enable_reviews = models.BooleanField(
        default=True,
        help_text="Enable/disable product reviews site-wide"
    )
    require_review_approval = models.BooleanField(
        default=True,
        help_text="Require admin approval for reviews"
    )
    min_review_length = models.IntegerField(
        default=10,
        help_text="Minimum character length for reviews"
    )
    max_reviews_per_user_per_product = models.IntegerField(
        default=1,
        help_text="Maximum reviews per user per product"
    )
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return "Site Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create site settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def get_currency_symbol(self):
        """Get the currency symbol for the selected currency"""
        return self.CURRENCY_SYMBOLS.get(self.default_currency, '₹')

    @property
    def currency_symbol(self):
        """Property to easily access currency symbol"""
        return self.get_currency_symbol()

    def save(self, *args, **kwargs):
        """Clear theme cache when settings are saved"""
        super().save(*args, **kwargs)
        # Clear theme cache to force reload
        try:
            from django.core.cache import cache
            cache.delete('current_theme')
        except:
            pass
