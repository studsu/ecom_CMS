from django.contrib import admin
from .plugins import plugin_manager


@admin.register(admin.site.get_app_list)
class PluginAdmin(admin.ModelAdmin):
    """
    Admin interface for managing plugins
    """
    pass


def register_plugin_admins():
    """
    Register all plugin admin interfaces
    """
    for plugin in plugin_manager.get_enabled_plugins().values():
        if hasattr(plugin, 'register_admin'):
            plugin.register_admin()