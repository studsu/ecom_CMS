from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def hello_world_header():
    """Display hello world message in header if plugin is active"""
    try:
        from plugins.models import PluginManager
        plugin = PluginManager.objects.get(app_name='plugins.hello_world')

        if plugin.is_active:
            return mark_safe('''
                <div class="alert alert-info text-center mb-0" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 0;">
                    <i class="fas fa-rocket"></i>
                    <strong>Hello World Plugin Active!</strong>
                    This message appears when the Hello World plugin is activated.
                    <i class="fas fa-star"></i>
                </div>
            ''')
        return ''
    except:
        return ''


@register.simple_tag
def plugin_status_badge():
    """Display plugin status badge"""
    try:
        from plugins.models import PluginManager
        plugin = PluginManager.objects.get(app_name='plugins.hello_world')

        if plugin.is_active:
            return mark_safe('<span class="badge bg-success">Hello World Plugin: Active</span>')
        else:
            return mark_safe('<span class="badge bg-secondary">Hello World Plugin: Inactive</span>')
    except:
        return mark_safe('<span class="badge bg-danger">Hello World Plugin: Not Found</span>')


@register.inclusion_tag('hello_world/plugin_info.html')
def hello_world_info():
    """Display plugin information"""
    try:
        from plugins.models import PluginManager
        plugin = PluginManager.objects.get(app_name='plugins.hello_world')
        return {
            'plugin': plugin,
            'is_active': plugin.is_active
        }
    except:
        return {
            'plugin': None,
            'is_active': False
        }