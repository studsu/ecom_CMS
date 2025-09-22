from django.shortcuts import render
from django.http import JsonResponse


def hello_world_message(request):
    """Return hello world message for homepage header"""
    return JsonResponse({
        'message': 'Hello World from Plugin!',
        'status': 'active'
    })


def plugin_status(request):
    """Check if the plugin is active"""
    from plugins.models import PluginManager

    try:
        plugin = PluginManager.objects.get(app_name='plugins.hello_world')
        return JsonResponse({
            'active': plugin.is_active,
            'name': plugin.name,
            'version': plugin.version
        })
    except PluginManager.DoesNotExist:
        return JsonResponse({
            'active': False,
            'error': 'Plugin not found'
        })