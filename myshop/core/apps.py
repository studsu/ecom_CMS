from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        from .plugins import plugin_manager
        plugin_manager.discover_and_load_plugins()