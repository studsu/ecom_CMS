from django.urls import path, include
from .plugins import plugin_manager


def get_plugin_urls():
    """
    Dynamically get all plugin URLs
    """
    return plugin_manager.get_plugin_urls()


urlpatterns = get_plugin_urls()