from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'unit_price', 'get_total_price')
    fields = ('product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'get_total_price')
    
    def get_total_price(self, obj):
        return f"₹{obj.get_total_price()}"
    get_total_price.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'shipping_name', 'email', 'status', 
        'payment_method', 'total_amount', 'created_at'
    ]
    list_filter = [
        'status', 'payment_method', 'payment_status', 'created_at', 
        'shipping_country', 'shipping_state'
    ]
    search_fields = [
        'order_number', 'email', 'phone', 'shipping_name', 
        'shipping_city', 'shipping_state'
    ]
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 
        'get_total_items', 'subtotal', 'tax_amount', 'total_amount'
    ]
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number', 'user', 'status', 'created_at', 'updated_at'
            )
        }),
        ('Customer Information', {
            'fields': (
                'email', 'phone'
            )
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_name', 'shipping_address_line_1', 'shipping_address_line_2',
                'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country'
            )
        }),
        ('Payment & Pricing', {
            'fields': (
                'payment_method', 'payment_status', 
                'subtotal', 'tax_amount', 'shipping_cost', 'total_amount'
            )
        }),
        ('Additional Information', {
            'fields': (
                'notes', 'get_total_items'
            )
        }),
    )
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'
    
    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} order(s) marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark selected orders as confirmed'
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} order(s) marked as processing.')
    mark_as_processing.short_description = 'Mark selected orders as processing'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = 'Mark selected orders as shipped'
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_as_delivered.short_description = 'Mark selected orders as delivered'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'unit_price', 'get_total_price']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['order__order_number', 'product_name', 'product_sku']
    readonly_fields = ['get_total_price']
    
    def get_total_price(self, obj):
        return f"₹{obj.get_total_price()}"
    get_total_price.short_description = 'Total Price'
