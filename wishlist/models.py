from django.db import models
from django.conf import settings
from catalog.models import Product


class Wishlist(models.Model):
    """User's wishlist to save favorite products"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return f"{self.user.username}'s Wishlist"

    @property
    def item_count(self):
        """Get total number of items in wishlist"""
        return self.items.filter(is_active=True).count()

    def add_product(self, product):
        """Add a product to wishlist"""
        item, created = WishlistItem.objects.get_or_create(
            wishlist=self,
            product=product,
            defaults={'is_active': True}
        )
        if not created and not item.is_active:
            item.is_active = True
            item.save()
        return item

    def remove_product(self, product):
        """Remove a product from wishlist"""
        try:
            item = WishlistItem.objects.get(wishlist=self, product=product)
            item.delete()
            return True
        except WishlistItem.DoesNotExist:
            return False

    def has_product(self, product):
        """Check if product is in wishlist"""
        return self.items.filter(product=product, is_active=True).exists()

    def clear(self):
        """Clear all items from wishlist"""
        self.items.all().delete()

    def get_active_items(self):
        """Get all active wishlist items"""
        return self.items.filter(is_active=True).select_related('product')


class WishlistItem(models.Model):
    """Individual items in a wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['wishlist', 'product']
        ordering = ['-added_at']
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.wishlist.user.username} - {self.product.title}"


class WishlistSettings(models.Model):
    """Settings for wishlist functionality"""
    enable_wishlist = models.BooleanField(
        default=True,
        help_text="Enable/disable wishlist functionality site-wide"
    )
    allow_guest_wishlist = models.BooleanField(
        default=False,
        help_text="Allow non-logged in users to use wishlist (stored in session)"
    )
    max_wishlist_items = models.PositiveIntegerField(
        default=100,
        help_text="Maximum number of items allowed in a wishlist (0 = unlimited)"
    )
    show_wishlist_count = models.BooleanField(
        default=True,
        help_text="Show wishlist item count in navigation"
    )
    enable_wishlist_sharing = models.BooleanField(
        default=True,
        help_text="Allow users to share their wishlist with others"
    )
    wishlist_expiry_days = models.PositiveIntegerField(
        default=365,
        help_text="Number of days after which inactive wishlist items expire (0 = never expire)"
    )

    class Meta:
        verbose_name = "Wishlist Settings"
        verbose_name_plural = "Wishlist Settings"

    def __str__(self):
        return "Wishlist Settings"

    @classmethod
    def get_settings(cls):
        """Get or create wishlist settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion of settings
        pass
