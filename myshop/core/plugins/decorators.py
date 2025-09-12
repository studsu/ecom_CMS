from functools import wraps
from django.http import HttpResponse
from django.shortcuts import render
from typing import Callable, Any

from . import plugin_manager


def plugin_required(plugin_name: str, fallback_template: str = None, fallback_message: str = None):
    """
    Decorator to ensure a plugin is enabled before executing a view
    
    Args:
        plugin_name: Name of the required plugin
        fallback_template: Template to render if plugin is not available
        fallback_message: Message to show if plugin is not available
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            plugin = plugin_manager.get_plugin(plugin_name)
            
            if not plugin or not plugin.enabled:
                if fallback_template:
                    return render(request, fallback_template, {
                        'message': fallback_message or f'Plugin {plugin_name} is not available',
                        'plugin_name': plugin_name
                    })
                else:
                    return HttpResponse(
                        fallback_message or f'Plugin {plugin_name} is not available',
                        status=503
                    )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def plugin_hook(hook_name: str, *hook_args, **hook_kwargs):
    """
    Decorator to create plugin hooks that other plugins can listen to
    
    Args:
        hook_name: Name of the hook
        *hook_args: Arguments to pass to hook listeners
        **hook_kwargs: Keyword arguments to pass to hook listeners
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Execute pre-hook listeners
            _execute_hook(f"pre_{hook_name}", request, *hook_args, **hook_kwargs)
            
            # Execute the original view
            response = view_func(request, *args, **kwargs)
            
            # Execute post-hook listeners
            _execute_hook(f"post_{hook_name}", request, response, *hook_args, **hook_kwargs)
            
            return response
        return wrapper
    return decorator


def _execute_hook(hook_name: str, *args, **kwargs):
    """
    Execute all registered hook listeners for a specific hook
    """
    for plugin in plugin_manager.get_enabled_plugins().values():
        hook_method = getattr(plugin, hook_name, None)
        if hook_method and callable(hook_method):
            try:
                hook_method(*args, **kwargs)
            except Exception as e:
                # Log error but don't break the flow
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error executing hook {hook_name} in plugin {plugin.name}: {str(e)}")


class PluginMiddleware:
    """
    Middleware to execute plugin hooks on every request
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Execute pre-request hooks
        _execute_hook('pre_request', request)
        
        # Process the request
        response = self.get_response(request)
        
        # Execute post-request hooks
        _execute_hook('post_request', request, response)
        
        return response