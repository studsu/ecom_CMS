from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, ProductReview, SiteSettings

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active")
    list_filter = ("is_active", "parent")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]
    fields = ("name", "slug", "parent", "description", "image", "is_active")

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2
    fields = ('image', 'alt_text', 'order', 'is_active')
    ordering = ('order',)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('name', 'value', 'price_adjustment', 'stock_quantity', 'is_active')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price", "sale_price", "stock_quantity", "is_active", "featured")
    list_filter = ("is_active", "featured", "category", "manage_stock")
    search_fields = ["title", "description", "sku"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("price", "sale_price", "stock_quantity", "is_active", "featured")
    inlines = [ProductImageInline, ProductVariantInline]
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "slug", "category", "short_description", "description")
        }),
        ("Pricing", {
            "fields": ("price", "sale_price")
        }),
        ("Inventory", {
            "fields": ("stock_quantity", "manage_stock", "sku")
        }),
        ("Media", {
            "fields": ("image",)
        }),
        ("Settings", {
            "fields": ("is_active", "featured", "weight")
        })
    )

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value', 'price_adjustment', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'name', 'product__category')
    search_fields = ['product__title', 'name', 'value']

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ['product__title', 'user__username', 'title', 'comment']
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
