from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.html import escape
from django.utils import timezone
from datetime import timedelta
from .models import Product, Cart, CartItem, Order, OrderItem, Category, BulkOrder, Review, ReviewHelpful
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import json


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        # Ensure session is saved for AJAX requests
        if not request.session.session_key:
            request.session.save()
            session_id = request.session.session_key
            
        cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart


# ─────────────────────────────
# 🔍 PRODUCT VIEWS
# ─────────────────────────────


def home(request):
    categories = Category.objects.all()
    # Pre-fetch products for homepage to avoid template query issues
    for category in categories:
        category.featured_products = category.product_set.filter(is_active=True)[:8]
    return render(request, 'store/home.html', {'categories': categories})


def product_list(request):
    category_slug = request.GET.get('category')
    category = None
    products = Product.objects.filter(is_active=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'store/product_list.html', {
        'products': products,
        'category': category,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Get approved reviews for the product
    all_reviews = Review.objects.filter(product=product, is_approved=True).select_related('user')
    
    # Check if user has already reviewed this product
    user_review = None
    if request.user.is_authenticated:
        user_review = all_reviews.filter(user=request.user).first()
    
    # Get reviews excluding user's own review
    reviews = all_reviews.exclude(user=request.user) if request.user.is_authenticated else all_reviews
    
    # Get other products from the same category, excluding the current product
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:8]  # Limit to 8 products
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'user_review': user_review,
        'other_reviews_count': reviews.count()
    })


def bulk_order_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        phone_number = request.POST.get('phone_number', '')
        message_text = request.POST.get('message', '')

        bulk_order = BulkOrder.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            quantity=quantity,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            message=message_text
        )

        # Send email notification to admin
        admin_email_subject = f"New Bulk Order Inquiry for {product.name}"
        admin_email_body = render_to_string('emails/bulk_order_admin_notification.html', {
            'bulk_order': bulk_order,
            'product': product,
            'user': request.user
        })
        admin_email = EmailMultiAlternatives(
            subject=admin_email_subject,
            body="New bulk order inquiry.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_NOTIFICATION_EMAIL],
        )
        admin_email.attach_alternative(admin_email_body, "text/html")
        admin_email.send()

        messages.success(request, f'Bulk order inquiry for {quantity} of {product.name} placed successfully!')
        return render(request, 'store/bulk_order.html', {'product': product})
    
    # Pre-fill form fields if user is authenticated
    initial_data = {}
    if request.user.is_authenticated:
        initial_data['full_name'] = f"{request.user.first_name} {request.user.last_name}".strip()
        initial_data['email'] = request.user.email
        initial_data['phone_number'] = request.user.phone if hasattr(request.user, 'phone') else ''

    return render(request, 'store/bulk_order.html', {'product': product, 'initial_data': initial_data})


# ─────────────────────────────
# 🛒 CART VIEWS
# ─────────────────────────────


def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('product_list')
        
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Ensure session exists for guest users
        if not request.user.is_authenticated and not request.session.session_key:
            request.session.create()
            
        cart = _get_or_create_cart(request)
        quantity = int(request.POST.get('quantity', 1))

        # Validate quantity input
        if quantity < 1 or quantity > 100:
            messages.error(request, "Invalid quantity.")
            return redirect('product_list')

        # Add or update cart item
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

        # Handle Buy Now action
        if request.POST.get('action') == 'buy':
            return redirect('checkout')

        # Regular form submission - redirect back
        next_url = request.GET.get('next') or 'view_cart'
        messages.success(request, f'{product.name} added to cart!')
        return redirect(next_url)
        
    except Exception as e:
        messages.error(request, "An error occurred while adding to cart.")
        return redirect('product_list')


def update_cart(request):
    cart = _get_or_create_cart(request)
    for item in cart.items.filter(is_saved=False).select_related('product'):
        qty = int(request.POST.get(f'quantity_{item.id}', item.quantity))
        if qty <= 0:
            item.delete()
        else:
            item.quantity = min(qty, 100)  # cap max qty
            item.save()

    if cart.items.filter(is_saved=False).count() == 0:
        cart.delete()

    return redirect('view_cart')


def view_cart(request):
    cart = _get_or_create_cart(request)
    cart_items = cart.items.filter(is_saved=False).select_related('product')
    saved_items = cart.items.filter(is_saved=True).select_related('product')

    return render(request, 'store/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'saved_items': saved_items
    })


def remove_cart_item(request, item_id):
    if request.method == "POST":
        cart = _get_or_create_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart = item.cart
        item.delete()

        if cart.items.filter(is_saved=False).count() == 0:
            response = HttpResponseRedirect(reverse('view_cart'))
            cart.delete()
            return response

    return redirect('view_cart')


def clear_cart(request):
    if request.method == "POST":
        cart = _get_or_create_cart(request)
        cart.items.filter(is_saved=False).delete()

        if cart.items.count() == 0:
            cart.delete()

    return redirect('view_cart')


# ─────────────────────────────
# 💾 SAVE FOR LATER
# ─────────────────────────────


def save_for_later(request, item_id):
    cart = _get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.is_saved = True
    item.save()
    return redirect('view_cart')


def move_to_cart(request, item_id):
    cart = _get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.is_saved = False
    item.save()
    return redirect('view_cart')


# ─────────────────────────────
# 🧾 ORDER + CHECKOUT
# ─────────────────────────────
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from accounts.models import Profile, CustomUser
from uuid import uuid4
from store.models import Cart, Order, OrderItem, Product
from payments.models import PhonePeOrder
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.common.exceptions import PhonePeException
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


from .forms import GuestCheckoutForm

def checkout(request):
    cart = _get_or_create_cart(request)
    cart_items = cart.items.filter(is_saved=False).select_related('product')

    if not cart_items.exists():
        return redirect('view_cart')

    if request.method == "POST":
        form = GuestCheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            if request.user.is_authenticated:
                email = request.user.email
                full_name = request.user.get_full_name()
                phone_number = getattr(request.user, 'phone', '')
                # You might need to adjust how you get address details for authenticated users
                address_line_1 = ''
                city = ''
                state = ''
                postal_code = ''
            else:
                email = form.cleaned_data['email']
                full_name = form.cleaned_data['full_name']
                phone_number = form.cleaned_data['phone_number']
                address_line_1 = form.cleaned_data['address_line_1']
                city = form.cleaned_data['city']
                state = form.cleaned_data['state']
                postal_code = form.cleaned_data['postal_code']

            # Get payment method from form
            payment_method = request.POST.get('payment_method', 'online')

            total = 0
            for item in cart_items:
                product = Product.objects.get(pk=item.product.pk)
                total += item.quantity * product.price

            # Set payment amount based on payment method
            if payment_method == 'cod':
                # For COD, customer pays 100 online as advance (logistics charge)
                payment_amount = 100
                cod_remaining = total - 100
            else:
                # For online payment, customer pays full amount
                payment_amount = total
                cod_remaining = None

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                address_line_1=address_line_1,
                city=city,
                state=state,
                postal_code=postal_code,
                total_amount=total,
                payment_method=payment_method,
                cod_remaining_amount=cod_remaining,
                status='initiated'
            )

            # Create order items
            for item in cart_items:
                product = Product.objects.get(pk=item.product.pk)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price
                )

            # Customer Email
            html_content = render_to_string("emails/order_confirmation_customer.html", {"user": request.user, "order": order})
            email_to = request.user.email if request.user.is_authenticated else email
            email = EmailMultiAlternatives(
                subject = f"Order #{order.id} Confirmation - {settings.SITE_NAME}",
                body="Thank you for your order.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_to],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            # Admin Alert
            if request.user.is_authenticated:
                user_info = request.user
            else:
                user_info = {
                    'full_name': form.cleaned_data['full_name'],
                    'email': form.cleaned_data['email'],
                }
            admin_html = render_to_string("emails/order_alert_admin.html", {"user": user_info, "order": order})
            admin_email = EmailMultiAlternatives(
                subject=f"New Order #{order.id}",
                body="New order placed.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.ADMIN_NOTIFICATION_EMAIL],
            )
            admin_email.attach_alternative(admin_html, "text/html")
            admin_email.send()

            cart_items.delete()
            if cart.items.count() == 0:
                cart.delete()

            if request.user.is_authenticated:
                try:
                    profile, _ = Profile.objects.get_or_create(user=request.user)
                    profile.shipping_address = shipping_address
                    profile.save()
                except:
                    pass

            merchant_order_id = str(uuid4())
            PhonePeOrder.objects.create(order=order, merchant_order_id=merchant_order_id)

            client = StandardCheckoutClient.get_instance(
                client_id=settings.PHONEPE_CLIENT_ID,
                client_secret=settings.PHONEPE_CLIENT_SECRET,
                client_version=settings.PHONEPE_CLIENT_VERSION,
                env=Env.SANDBOX if settings.PHONEPE_ENV == 'SANDBOX' else Env.PRODUCTION,
                should_publish_events=False
            )

            pay_request = StandardCheckoutPayRequest.build_request(
                merchant_order_id=merchant_order_id,
                amount=int(payment_amount * 100),
                redirect_url=settings.PHONEPE_REDIRECT_URL,
                meta_info=MetaInfo(udf1=str(request.user.id) if request.user.is_authenticated else None)
            )

            try:
                pay_response = client.pay(pay_request)
                return redirect(pay_response.redirect_url)
            except PhonePeException as e:
                return HttpResponse(f"Payment Error: {e.message}", status=500)
    else:
        form = GuestCheckoutForm(user=request.user)

    return render(request, 'store/checkout.html', {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
    })



@login_required
def order_success(request):
    return render(request, 'store/order_success.html')


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})



def payment_policy(request):
    return render(request, "store/policies/payment_policy.html")

def shipping_policy(request):
    return render(request, "store/policies/shipping_policy.html")

def return_policy(request):
    return render(request, "store/policies/return_policy.html")

def terms_and_conditions(request):
    return render(request, "store/policies/terms_and_conditions.html")

def privacy_policy(request):
    return render(request, "store/policies/privacy_policy.html")


from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from .forms import ContactMessageForm, ReviewForm
from .models import ContactMessage
from django.conf import settings

def contact_view(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact = form.save()
            # Confirmation message
            messages.success(request, "Your message has been sent successfully!")

            # Email to admin
            send_mail(
                subject=f"New Contact Message: {contact.subject}",
                message=f"From: {contact.name} <{contact.email}>\n\n{contact.message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
                fail_silently=True,
            )

            # Optional: Email to user
            send_mail(
                subject="Thank you for contacting us!",
                message=f"Hi {contact.name},\n\nThank you for reaching out to us. We have received your message and will respond shortly.\n\nRegards,\nSmokeKing.in",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact.email],
                fail_silently=True,
            )

            return redirect('contact_us')
    else:
        form = ContactMessageForm()

    return render(request, 'store/contact.html', {'form': form})

def robots_txt(request):
    return HttpResponse(render_to_string('robots.txt', {}, request=request), content_type="text/plain")


@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Rate limiting: Check if user has submitted a review in the last hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_reviews = Review.objects.filter(
        user=request.user,
        created_at__gte=one_hour_ago
    ).count()
    
    if recent_reviews >= 3:  # Max 3 reviews per hour
        messages.error(request, "You're submitting reviews too quickly. Please wait before submitting another review.")
        return redirect('product_detail', slug=slug)
    
    # Check if user already has a review for this product
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.error(request, "You have already reviewed this product.")
        return redirect('product_detail', slug=slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Your review has been submitted successfully! It will be published after approval.")
            return redirect('product_detail', slug=slug)
    else:
        form = ReviewForm()
    
    return render(request, 'store/add_review.html', {
        'form': form,
        'product': product
    })


@login_required
def edit_review(request, slug, review_id):
    product = get_object_or_404(Product, slug=slug)
    review = get_object_or_404(Review, id=review_id, product=product, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated successfully!")
            return redirect('product_detail', slug=slug)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'store/edit_review.html', {
        'form': form,
        'product': product,
        'review': review
    })


@login_required
def delete_review(request, slug, review_id):
    product = get_object_or_404(Product, slug=slug)
    review = get_object_or_404(Review, id=review_id, product=product, user=request.user)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, "Your review has been deleted.")
    
    return redirect('product_detail', slug=slug)


@login_required
def toggle_review_helpful(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    # Validate review_id is integer and reasonable
    try:
        review_id = int(review_id)
        if review_id <= 0 or review_id > 999999999:  # Reasonable bounds
            return JsonResponse({'error': 'Invalid review ID'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid review ID'}, status=400)
    
    review = get_object_or_404(Review, id=review_id, is_approved=True)
    
    # Prevent users from voting on their own reviews
    if review.user == request.user:
        return JsonResponse({'error': 'Cannot vote on your own review'}, status=400)
    
    # Rate limiting for helpful votes
    one_minute_ago = timezone.now() - timedelta(minutes=1)
    recent_votes = ReviewHelpful.objects.filter(
        user=request.user,
        created_at__gte=one_minute_ago
    ).count()
    
    if recent_votes >= 10:  # Max 10 votes per minute
        return JsonResponse({'error': 'Too many votes. Please wait before voting again.'}, status=429)
    
    helpful_vote, created = ReviewHelpful.objects.get_or_create(
        review=review,
        user=request.user,
        defaults={'is_helpful': True}
    )
    
    if not created:
        # Toggle the vote or remove it
        if request.POST.get('action') == 'remove':
            helpful_vote.delete()
            action = 'removed'
        else:
            helpful_vote.is_helpful = not helpful_vote.is_helpful
            helpful_vote.save()
            action = 'helpful' if helpful_vote.is_helpful else 'not_helpful'
    else:
        action = 'helpful'
    
    # Update helpful count on review
    helpful_count = review.helpful_votes.filter(is_helpful=True).count()
    review.helpful_count = helpful_count
    review.save()
    
    return JsonResponse({
        'action': action,
        'helpful_count': helpful_count,
        'user_vote': helpful_vote.is_helpful if helpful_vote else None
    })