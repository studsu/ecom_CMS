from django.contrib import admin
from django.utils.html import format_html
from .models import Wishlist, WishlistItem, WishlistSettings


@admin.register(WishlistSettings)
class WishlistSettingsAdmin(admin.ModelAdmin):
    """Admin interface for wishlist settings"""

    def has_add_permission(self, request):
        # Only allow one settings instance
        return not WishlistSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False

    def changelist_view(self, request, extra_context=None):
        # Redirect to edit view if settings exist
        if WishlistSettings.objects.exists():
            settings = WishlistSettings.objects.first()
            return self.change_view(request, str(settings.pk))
        return super().changelist_view(request, extra_context)

    fieldsets = (
        ('Basic Settings', {
            'fields': ('enable_wishlist', 'show_wishlist_count'),
            'description': 'Core wishlist functionality settings'
        }),
        ('User Permissions', {
            'fields': ('allow_guest_wishlist', 'max_wishlist_items'),
            'description': 'Control who can use wishlist and limits'
        }),
        ('Advanced Features', {
            'fields': ('enable_wishlist_sharing', 'wishlist_expiry_days'),
            'description': 'Additional wishlist features'
        }),
    )


class WishlistItemInline(admin.TabularInline):
    """Inline admin for wishlist items"""
    model = WishlistItem
    extra = 0
    readonly_fields = ('added_at',)
    raw_id_fields = ('product',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Admin interface for wishlists"""
    list_display = ('user', 'item_count_display', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'item_count_display')
    inlines = [WishlistItemInline]

    def item_count_display(self, obj):
        """Display item count with formatting"""
        count = obj.item_count
        if count == 0:
            return format_html('<span style="color: #999;">Empty</span>')
        elif count > 50:
            return format_html('<span style="color: #d63384; font-weight: bold;">{} items</span>', count)
        else:
            return format_html('<span style="color: #198754;">{} items</span>', count)

    item_count_display.short_description = 'Items'
    item_count_display.admin_order_field = 'items__count'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    """Admin interface for individual wishlist items"""
    list_display = ('wishlist_user', 'product', 'is_active', 'added_at')
    list_filter = ('is_active', 'added_at', 'product__category')
    search_fields = ('wishlist__user__username', 'product__title', 'product__sku')
    readonly_fields = ('added_at',)
    raw_id_fields = ('wishlist', 'product')
    list_editable = ('is_active',)

    def wishlist_user(self, obj):
        """Display wishlist owner"""
        return obj.wishlist.user.username
    wishlist_user.short_description = 'User'
    wishlist_user.admin_order_field = 'wishlist__user__username'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wishlist__user', 'product')


# Customize admin site header
admin.site.site_header = "Glam Jewelry Admin"
admin.site.site_title = "Glam Admin"
admin.site.index_title = "Welcome to Glam Jewelry Administration"
