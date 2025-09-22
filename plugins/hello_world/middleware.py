from django.utils.deprecation import MiddlewareMixin


class HelloWorldMiddleware(MiddlewareMixin):
    """Middleware to add hello world plugin status to request context"""

    def process_request(self, request):
        """Add hello world plugin status to request"""
        try:
            from plugins.models import PluginManager
            plugin = PluginManager.objects.get(app_name='plugins.hello_world')
            request.hello_world_active = plugin.is_active
        except:
            request.hello_world_active = False

        return None