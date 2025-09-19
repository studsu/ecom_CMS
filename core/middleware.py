from django.conf import settings
from django.core.cache import cache


class DynamicStaticThemeMiddleware:
    """
    Middleware to dynamically set static file directories based on theme setting from database
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the theme from the database with caching
        theme = cache.get('current_theme')

        if theme is None:
            try:
                from catalog.models import SiteSettings
                site_settings = SiteSettings.get_settings()
                theme = site_settings.theme
                cache.set('current_theme', theme, 30)  # Cache for 30 seconds
            except:
                # Fallback to default theme if database is not available
                theme = 'glam'

        # Update static files directories for theme-specific static files
        theme_static_dir = settings.BASE_DIR / "themes" / theme / "static"
        if len(settings.STATICFILES_DIRS) >= 2:
            # Update the theme-specific static directory (second item)
            settings.STATICFILES_DIRS[1] = theme_static_dir
        else:
            # Fallback: recreate the list if it's not as expected
            settings.STATICFILES_DIRS = [
                settings.BASE_DIR / "static_shared",
                theme_static_dir,
            ]

        response = self.get_response(request)
        return response