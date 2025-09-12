from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist, SiteSettings, BulkOrder, Review, ReviewHelpful
from django.utils.html import format_html

from django.contrib import admin

admin.site.site_header = "MyShop Admin"
admin.site.site_title = "MyShop Admin Panel"
admin.site.index_title = "Welcome to MyShop Dashboard"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'banner', 'mobile_banner']
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'banner', 'mobile_banner')
        }),
        ('SEO Options', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )


from django.contrib import admin
from .models import Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['name', 'category', 'price', 'stock']
#     inlines = [ProductImageInline]

    
admin.site.register(Cart)
admin.site.register(CartItem)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_display', 'email', 'phone_number', 'status', 'tracking_id', 'total_amount', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['id', 'user__username', 'email', 'phone_number', 'full_name', 'tracking_id']
    readonly_fields = ['id', 'total_amount', 'created_at', 'updated_at']
    list_editable = ['status', 'tracking_id']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'user', 'status', 'tracking_id', 'seller_remark', 'total_amount', 'payment_method', 'cod_remaining_amount')
        }),
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Shipping Address', {
            'fields': ('address_line_1', 'city', 'state', 'postal_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        return obj.user.username if obj.user else obj.full_name
    user_display.short_description = 'Customer'
    
    actions = ['mark_as_shipped', 'mark_as_delivered', 'mark_as_processing']
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_as_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} order(s) marked as processing.')
    mark_as_processing.short_description = "Mark selected orders as processing"
    
    def save_model(self, request, obj, form, change):
        if change:  # Only for updates, not new orders
            # Check if tracking_id or status changed to trigger notifications
            if 'tracking_id' in form.changed_data or 'status' in form.changed_data:
                self.message_user(request, 
                    'Order updated successfully. Customer will be notified via email if tracking information was added or status changed to shipped.', 
                    level='success')
        super().save_model(request, obj, form, change)

admin.site.register(OrderItem)
admin.site.register(Wishlist)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'logo',)

    def has_add_permission(self, request):
        # Allow only one instance of SiteSettings
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the single instance
        return False

@admin.register(BulkOrder)
class BulkOrderAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'quantity', 'full_name', 'email', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product__name', 'full_name', 'email', 'phone_number')
    readonly_fields = ('created_at',)


import csv, os
from urllib.request import urlopen
from urllib.parse import urlparse

from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.utils.text import slugify

from .models import Product, Category, ProductImage

# 🔹 Inline for extra images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

# 🔹 Upload form
class ProductCSVForm(forms.Form):
    csv_file = forms.FileField()

# 🔹 Utility for main image path
def get_main_image_upload_path(product_id, filename):
    return f'gallery/productimages/{product_id}/main_{filename}'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_active']
    list_editable = ['stock', 'is_active']
    search_fields = ['name', 'description']
    list_filter = ['category', 'is_active']
    inlines = [ProductImageInline]
    change_list_template = "admin/store/product_changelist.html"
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'short_description', 'description', 'price', 'stock', 'wholesale_price', 'min_wholesale_quantity', 'image', 'gif', 'is_active')
        }),
        ('SEO Options', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-woo/", self.admin_site.admin_view(self.import_woo_csv), name="import_woo_csv"),
            path("import-custom/", self.admin_site.admin_view(self.import_custom_csv), name="import_custom_csv"),
            path("download-woo-template/", self.admin_site.admin_view(self.download_woo_template), name="download_woo_template"),
            path("download-custom-template/", self.admin_site.admin_view(self.download_custom_template), name="download_custom_template"),
        ]
        return custom_urls + urls

    def download_woo_template(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=woo_template.csv'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Description', 'Regular price', 'Categories', 'Images'])
        writer.writerow(['Sample Product', 'Short desc', '499', 'DIARY', 'https://example.com/img1.jpg, https://example.com/img2.jpg'])
        return response

    def download_custom_template(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=custom_template.csv'
        writer = csv.writer(response)
        writer.writerow(['name', 'slug', 'category', 'description', 'price', 'stock', 'image', 'is_active', 'images'])
        writer.writerow(['Custom Product', 'custom-product', 'DIARY', 'Full desc here', '399', '20', '', 'True', 'https://example.com/img1.jpg, https://example.com/img2.jpg'])
        return response

    def import_woo_csv(self, request):
        return self._handle_import_csv(request, is_woo=True)

    def import_custom_csv(self, request):
        return self._handle_import_csv(request, is_woo=False)

    def _handle_import_csv(self, request, is_woo=False):
        if request.method == "POST":
            form = ProductCSVForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                try:
                    decoded = csv_file.read().decode('utf-8').splitlines()
                except UnicodeDecodeError:
                    csv_file.seek(0)
                    decoded = csv_file.read().decode('latin1').splitlines()
                reader = csv.DictReader(decoded)
                count = 0

                for row in reader:
                    if is_woo:
                        name = row.get('Name')
                        slug = slugify(name)
                        category_name = row.get('Categories', 'Uncategorized')
                        price = row.get('Regular price') or 0
                        description = row.get('Description', '')
                        image_urls = row.get('Images', '').split(',')
                    else:
                        name = row.get('name')
                        slug = row.get('slug') or slugify(name)
                        category_name = row.get('category', 'Uncategorized')
                        price = row.get('price', 0)
                        description = row.get('description', '')
                        image_urls = row.get('images', '').split(',')

                    image_urls = [url.strip() for url in image_urls if url.strip()]
                    category, _ = Category.objects.get_or_create(name=category_name)

                    # 🔹 Step 1: create product without image
                    product = Product.objects.create(
                        name=name,
                        slug=slug,
                        category=category,
                        price=price,
                        description=description,
                        stock=row.get('stock', 10),
                        is_active=row.get('is_active', 'True').lower() in ['true', '1'],
                    )

                    # 🔹 Step 2: Save main image
                    if image_urls:
                        try:
                            response = urlopen(image_urls[0])
                            filename = os.path.basename(urlparse(image_urls[0]).path)
                            file_content = ContentFile(response.read())
                            product.image.save(f"main_{filename}", file_content, save=True)
                        except Exception as e:
                            print(f"⚠️ Error downloading main image: {e}")

                    # 🔹 Step 3: Save gallery images (excluding first)
                    for img_url in image_urls[1:]:
                        try:
                            if img_url.startswith("http"):
                                response = urlopen(img_url)
                                filename = os.path.basename(urlparse(img_url).path)
                                img_file = ContentFile(response.read())
                                product_image = ProductImage(product=product)
                                product_image.image.save(filename, img_file, save=True)
                        except Exception as e:
                            print(f"⚠️ Error downloading gallery image: {e}")

                    count += 1

                self.message_user(request, f"✅ Successfully imported {count} products.", messages.SUCCESS)
                return redirect("..")
        else:
            form = ProductCSVForm()

        return render(request, "admin/store/import_products_form.html", {
            "form": form,
            "is_woo": is_woo
        })


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'title', 'is_verified_purchase', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__username', 'title', 'review']
    readonly_fields = ['is_verified_purchase', 'created_at', 'updated_at']
    list_editable = ['is_approved']
    ordering = ['-created_at']
    actions = ['approve_reviews', 'disapprove_reviews']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'user')
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} review(s) were successfully approved.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def disapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} review(s) were successfully disapproved.')
    disapprove_reviews.short_description = "Disapprove selected reviews"
    
    def changelist_view(self, request, extra_context=None):
        # Add pending reviews count to the context
        pending_count = Review.objects.filter(is_approved=False).count()
        extra_context = extra_context or {}
        extra_context['pending_reviews_count'] = pending_count
        return super().changelist_view(request, extra_context)


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'is_helpful', 'created_at']
    list_filter = ['is_helpful', 'created_at']
    search_fields = ['review__product__name', 'user__username']
    readonly_fields = ['created_at']