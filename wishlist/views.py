from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from catalog.models import Product
from .models import Wishlist, WishlistItem, WishlistSettings
import json


def get_or_create_wishlist(user):
    """Get or create a wishlist for the user"""
    if user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=user)
        return wishlist
    return None


@login_required
def wishlist_view(request):
    """Display the user's wishlist"""
    settings = WishlistSettings.get_settings()

    if not settings.enable_wishlist:
        messages.error(request, "Wishlist functionality is currently disabled.")
        return redirect('core:home')

    wishlist = get_or_create_wishlist(request.user)
    items = wishlist.get_active_items() if wishlist else []

    # Pagination
    paginator = Paginator(items, 12)  # Show 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'wishlist': wishlist,
        'items': page_obj,
        'settings': settings,
        'total_items': len(items),
    }

    return render(request, 'wishlist/wishlist.html', context)


@require_POST
@login_required
def add_to_wishlist(request):
    """Add a product to wishlist via AJAX"""
    settings = WishlistSettings.get_settings()

    if not settings.enable_wishlist:
        return JsonResponse({
            'success': False,
            'message': 'Wishlist functionality is currently disabled.'
        })

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        if not product_id:
            return JsonResponse({
                'success': False,
                'message': 'Product ID is required.'
            })

        product = get_object_or_404(Product, id=product_id, is_active=True)
        wishlist = get_or_create_wishlist(request.user)

        if not wishlist:
            return JsonResponse({
                'success': False,
                'message': 'Please log in to use wishlist.'
            })

        # Check if already in wishlist
        if wishlist.has_product(product):
            return JsonResponse({
                'success': False,
                'message': f'{product.title} is already in your wishlist.',
                'already_in_wishlist': True
            })

        # Check max items limit
        if settings.max_wishlist_items > 0 and wishlist.item_count >= settings.max_wishlist_items:
            return JsonResponse({
                'success': False,
                'message': f'Maximum {settings.max_wishlist_items} items allowed in wishlist.'
            })

        # Add to wishlist
        wishlist.add_product(product)

        return JsonResponse({
            'success': True,
            'message': f'{product.title} added to your wishlist!',
            'wishlist_count': wishlist.item_count
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while adding to wishlist.'
        })


@require_POST
@login_required
def remove_from_wishlist(request):
    """Remove a product from wishlist via AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        if not product_id:
            return JsonResponse({
                'success': False,
                'message': 'Product ID is required.'
            })

        product = get_object_or_404(Product, id=product_id)
        wishlist = get_or_create_wishlist(request.user)

        if not wishlist:
            return JsonResponse({
                'success': False,
                'message': 'Wishlist not found.'
            })

        success = wishlist.remove_product(product)

        if success:
            return JsonResponse({
                'success': True,
                'message': f'{product.title} removed from your wishlist.',
                'wishlist_count': wishlist.item_count
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Product not found in wishlist.'
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while removing from wishlist.'
        })


@require_POST
@login_required
def clear_wishlist(request):
    """Clear all items from wishlist"""
    try:
        wishlist = get_or_create_wishlist(request.user)

        if wishlist:
            item_count = wishlist.item_count
            wishlist.clear()

            return JsonResponse({
                'success': True,
                'message': f'Cleared {item_count} items from your wishlist.',
                'wishlist_count': 0
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Wishlist not found.'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while clearing wishlist.'
        })


@login_required
def wishlist_count(request):
    """Get current wishlist count via AJAX"""
    wishlist = get_or_create_wishlist(request.user)
    count = wishlist.item_count if wishlist else 0

    return JsonResponse({
        'count': count
    })


@login_required
def share_wishlist(request):
    """Share wishlist functionality"""
    settings = WishlistSettings.get_settings()

    if not settings.enable_wishlist_sharing:
        messages.error(request, "Wishlist sharing is currently disabled.")
        return redirect('wishlist:wishlist')

    wishlist = get_or_create_wishlist(request.user)

    if not wishlist or wishlist.item_count == 0:
        messages.warning(request, "Your wishlist is empty. Add some items to share!")
        return redirect('wishlist:wishlist')

    # Generate a shareable link or handle sharing logic
    share_url = request.build_absolute_uri(f'/wishlist/shared/{wishlist.user.username}/')

    context = {
        'wishlist': wishlist,
        'share_url': share_url,
        'settings': settings,
    }

    return render(request, 'wishlist/share.html', context)
