from django.conf import settings

def site_context(request):
    from catalog.models import Category

    # Get main categories for navigation
    main_categories = Category.objects.filter(is_active=True, parent=None)[:8]

    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "Ecom_CMS"),
        "THEME": getattr(settings, "THEME", "default"),
        "main_categories": main_categories,
    }
