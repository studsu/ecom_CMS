"""
Dynamic Admin Configuration
Updates admin header based on SiteSettings
"""

from django.contrib import admin
from django.core.cache import cache


def get_dynamic_site_name():
    """Get site name from SiteSettings with caching"""
    cached_name = cache.get('admin_site_name')
    if cached_name:
        return cached_name
    
    try:
        from catalog.models import SiteSettings
        site_settings = SiteSettings.get_settings()
        site_name = site_settings.site_name or "Ecom CMS"
        
        # Cache for 5 minutes
        cache.set('admin_site_name', site_name, 300)
        return site_name
        
    except Exception:
        # Fallback if SiteSettings doesn't exist yet
        return "Ecom CMS"


def update_admin_site():
    """Update admin site headers with dynamic site name"""
    site_name = get_dynamic_site_name()
    
    admin.site.site_header = f"{site_name} Administration"
    admin.site.site_title = f"{site_name} Admin"
    admin.site.index_title = f"Welcome to {site_name} Administration"


class DynamicAdminSite(admin.AdminSite):
    """Custom admin site that updates headers dynamically"""
    
    def index(self, request, extra_context=None):
        """Override index to update headers on each load"""
        update_admin_site()
        return super().index(request, extra_context)
    
    def app_index(self, request, app_label, extra_context=None):
        """Override app index to update headers"""
        update_admin_site()
        return super().app_index(request, app_label, extra_context)


# Initialize on import
update_admin_site()