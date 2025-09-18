from django.conf import settings

def site_context(request):
    from catalog.models import Category

    # Get main categories for navigation
    main_categories = Category.objects.filter(is_active=True, parent=None)[:8]

    # Get user's wishlist count
    wishlist_count = 0
    if request.user.is_authenticated:
        try:
            from wishlist.models import Wishlist
            wishlist = Wishlist.objects.filter(user=request.user).first()
            if wishlist:
                wishlist_count = wishlist.item_count
        except:
            wishlist_count = 0

    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "Ecom_CMS"),
        "THEME": getattr(settings, "THEME", "default"),
        "main_categories": main_categories,
        "wishlist_count": wishlist_count,
    }
