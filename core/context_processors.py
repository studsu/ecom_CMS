from django.conf import settings

def site_context(request):
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "Ecom_CMS"),
        "THEME": getattr(settings, "THEME", "default"),
    }
