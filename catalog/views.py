from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from .models import Product, Category, ProductReview, SiteSettings
from .cart import Cart

def product_list(request):
    # Get all active products
    qs = Product.objects.filter(is_active=True).select_related("category")
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        qs = qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Category filtering
    category_slug = request.GET.get('category', '')
    selected_category = None
    if category_slug:
        try:
            selected_category = Category.objects.get(slug=category_slug, is_active=True)
            # Include products from child categories
            category_ids = [selected_category.id]
            category_ids.extend([child.id for child in selected_category.get_all_children()])
            qs = qs.filter(category__id__in=category_ids)
        except Category.DoesNotExist:
            pass
    
    # Price filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            qs = qs.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            qs = qs.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = {
        'name': 'title',
        '-name': '-title',
        'price': 'price',
        '-price': '-price',
        'newest': '-created_at',
        'oldest': 'created_at',
        'featured': '-featured'
    }
    
    if sort_by in valid_sorts:
        qs = qs.order_by(valid_sorts[sort_by])
    else:
        qs = qs.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(qs, 12)  # 12 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = Category.objects.filter(is_active=True, parent=None)
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'current_sort': sort_by,
        'total_products': qs.count()
    }
    
    return render(request, "catalog/product_list.html", context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get site settings for reviews
    site_settings = SiteSettings.get_settings()
    
    # Get product variants
    variants = product.variants.filter(is_active=True)
    
    # Get related products
    related_products = product.get_related_products()
    
    # Get approved reviews
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    
    # Check if user has already reviewed this product
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = ProductReview.objects.filter(
            product=product, 
            user=request.user
        ).exists()
    
    context = {
        'product': product,
        'variants': variants,
        'related_products': related_products,
        'reviews': reviews,
        'site_settings': site_settings,
        'user_has_reviewed': user_has_reviewed,
        'average_rating': product.get_average_rating(),
        'review_count': product.get_review_count()
    }
    
    return render(request, "catalog/product_detail.html", context)

@login_required
@require_POST
def add_review(request, product_id):
    """Add a product review"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    site_settings = SiteSettings.get_settings()
    
    # Check if reviews are enabled
    if not site_settings.enable_reviews:
        messages.error(request, "Product reviews are currently disabled.")
        return redirect('product_detail', slug=product.slug)
    
    # Check if user already reviewed this product
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        messages.error(request, "You have already reviewed this product.")
        return redirect('product_detail', slug=product.slug)
    
    # Get form data
    rating = request.POST.get('rating')
    title = request.POST.get('title', '').strip()
    comment = request.POST.get('comment', '').strip()
    
    # Validate data
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError()
    except (ValueError, TypeError):
        messages.error(request, "Please select a valid rating (1-5 stars).")
        return redirect('product_detail', slug=product.slug)
    
    if not title:
        messages.error(request, "Please provide a review title.")
        return redirect('product_detail', slug=product.slug)
    
    if len(comment) < site_settings.min_review_length:
        messages.error(request, f"Review must be at least {site_settings.min_review_length} characters long.")
        return redirect('product_detail', slug=product.slug)
    
    # Create review
    review = ProductReview.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        title=title,
        comment=comment,
        is_approved=not site_settings.require_review_approval
    )
    
    if site_settings.require_review_approval:
        messages.success(request, "Thank you for your review! It will be published after admin approval.")
    else:
        messages.success(request, "Thank you for your review!")
    
    return redirect('product_detail', slug=product.slug)

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is in stock
    if not product.is_in_stock:
        messages.error(request, f"Sorry, {product.title} is out of stock.")
        return redirect('product_detail', slug=product.slug)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if we have enough stock
    if product.manage_stock and quantity > product.stock_quantity:
        messages.error(request, f"Sorry, only {product.stock_quantity} items available for {product.title}.")
        return redirect('product_detail', slug=product.slug)
    
    cart.add(product=product, quantity=quantity)
    messages.success(request, f"Added {quantity} x {product.title} to cart.")
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Added {quantity} x {product.title} to cart.",
            'cart_count': len(cart)
        })
    
    return redirect('product_detail', slug=product.slug)

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'catalog/cart_detail.html', {'cart': cart})

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f"Removed {product.title} from cart.")
    return redirect('cart_detail')

@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart.remove(product)
        messages.success(request, f"Removed {product.title} from cart.")
    else:
        # Check stock availability
        if product.manage_stock and quantity > product.stock_quantity:
            messages.error(request, f"Sorry, only {product.stock_quantity} items available for {product.title}.")
            return redirect('cart_detail')
        
        cart.update_quantity(product, quantity)
        messages.success(request, f"Updated {product.title} quantity to {quantity}.")
    
    return redirect('cart_detail')
