from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.conf import settings
from django.core.cache import cache


class DynamicThemeLoader(FilesystemLoader):
    """
    Custom template loader that dynamically loads templates based on theme setting from database
    """

    def get_dirs(self):
        """Get template directories based on current theme from database"""
        # Cache the theme for 30 seconds to avoid database hits on every template load
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

        # Return theme-specific template directories
        return [
            settings.BASE_DIR / "themes" / theme,
            settings.BASE_DIR / "templates_shared",
        ]