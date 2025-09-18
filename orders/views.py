from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Order, OrderItem
from .forms import OrderForm
from catalog.cart import Cart
from catalog.models import Product


def checkout(request):
    """Checkout view to place an order"""
    cart = Cart(request)
    
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('catalog:cart_detail')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Create order
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.save()
            
            # Create order items and reduce stock
            for item in cart:
                # Create order item with variant support
                variant = item.get('variant')
                order_item = OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_variant=variant,
                    product_name=item['product'].title,
                    product_sku=getattr(item['product'], 'sku', '') or '',
                    variant_name=variant.name if variant else None,
                    variant_value=variant.value if variant else None,
                    quantity=item['quantity'],
                    unit_price=item['price']
                )

                # Reduce stock quantities
                if item.get('variant'):
                    # Reduce variant stock if variant was selected
                    variant = item['variant']
                    if not variant.reduce_stock(item['quantity']):
                        # This shouldn't happen due to cart validation, but handle gracefully
                        messages.warning(request, f"Insufficient stock for {item['product'].title} ({variant.name}: {variant.value})")
                else:
                    # Reduce main product stock if no variant
                    product = item['product']
                    if product.manage_stock:
                        if not product.reduce_stock(item['quantity']):
                            messages.warning(request, f"Insufficient stock for {item['product'].title}")
            
            # Calculate totals
            order.calculate_total()
            
            # Clear cart
            cart.clear()
            
            messages.success(request, f'Your order #{order.order_number} has been placed successfully!')
            return redirect('orders:order_success', order_number=order.order_number)
    else:
        form = OrderForm()
        # Pre-fill user data if authenticated
        if request.user.is_authenticated:
            # Basic user info
            form.fields['email'].initial = request.user.email
            full_name = f"{request.user.first_name} {request.user.last_name}".strip()
            if full_name:
                form.fields['shipping_name'].initial = full_name
            
            # Get phone from user profile
            try:
                profile = request.user.profile
                if profile.phone:
                    form.fields['phone'].initial = profile.phone
            except:
                pass
            
            # Pre-fill address from user's default shipping address
            try:
                default_address = request.user.addresses.filter(
                    type='shipping', is_default=True
                ).first()
                if default_address:
                    form.fields['shipping_name'].initial = default_address.name
                    form.fields['shipping_address_line_1'].initial = default_address.street
                    form.fields['shipping_city'].initial = default_address.city
                    form.fields['shipping_state'].initial = default_address.state
                    form.fields['shipping_postal_code'].initial = default_address.postal_code
                    form.fields['shipping_country'].initial = default_address.country
            except:
                pass
    
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'form': form,
        'cart_total': cart.get_total_price(),
    })


def order_success(request, order_number):
    """Order success confirmation page"""
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/order_success.html', {
        'order': order,
    })


@login_required
def order_history(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {
        'orders': orders,
    })


def order_detail(request, order_number):
    """Order detail view"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Allow access if user owns the order or if not authenticated (for guest orders)
    if request.user.is_authenticated and order.user and order.user != request.user:
        messages.error(request, 'You do not have permission to view this order.')
        return redirect('core:home')
    
    return render(request, 'orders/order_detail.html', {
        'order': order,
    })
