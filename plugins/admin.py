from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Review, PluginManager

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_public", "created_at")
    list_filter = ("is_public", "rating", "created_at")
    search_fields = ("product__title", "user__username", "title", "comment")
    autocomplete_fields = ("product", "user")


@admin.register(PluginManager)
class PluginManagerAdmin(admin.ModelAdmin):
    """Admin interface for managing plugins"""
    
    list_display = ('name', 'version', 'status_display', 'action_buttons', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    search_fields = ('name', 'app_name', 'description')
    readonly_fields = ('app_name', 'plugin_path', 'created_at', 'updated_at')
    
    change_list_template = 'admin/plugins/pluginmanager/change_list.html'
    
    def has_add_permission(self, request):
        return False  # Plugins are discovered automatically
    
    def has_delete_permission(self, request, obj=None):
        return False  # Don't allow deletion of plugin records
    
    def status_display(self, obj):
        """Display plugin status with color coding"""
        if obj.is_active:
            return format_html('<span style="color: #28a745; font-weight: bold;">🟢 Active</span>')
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">🔴 Inactive</span>')
    status_display.short_description = 'Status'
    
    def action_buttons(self, obj):
        """Display activate/deactivate buttons"""
        if obj.is_active:
            return format_html(
                '<a href="?action=deactivate&plugin_id={}" class="button" style="background: #dc3545; color: white;">Deactivate</a>',
                obj.id
            )
        else:
            return format_html(
                '<a href="?action=activate&plugin_id={}" class="button" style="background: #28a745; color: white;">Activate</a>',
                obj.id
            )
    action_buttons.short_description = 'Actions'
    
    def changelist_view(self, request, extra_context=None):
        """Handle plugin activation/deactivation and discovery"""
        
        # Handle plugin discovery
        if request.GET.get('action') == 'discover':
            PluginManager.discover_plugins()
            messages.success(request, "🔍 Plugin discovery completed. All plugins have been scanned.")
            return HttpResponseRedirect(request.path)
        
        # Handle plugin activation/deactivation
        action = request.GET.get('action')
        plugin_id = request.GET.get('plugin_id')
        
        if action and plugin_id:
            try:
                plugin = PluginManager.objects.get(id=plugin_id)
                
                if action == 'activate':
                    plugin.activate()
                    messages.success(request, f"✅ Plugin '{plugin.name}' has been activated. Restart the server to apply changes.")
                elif action == 'deactivate':
                    plugin.deactivate()
                    messages.warning(request, f"⚠️ Plugin '{plugin.name}' has been deactivated. Restart the server to apply changes.")
                
                return HttpResponseRedirect(request.path)
            except PluginManager.DoesNotExist:
                messages.error(request, "Plugin not found.")
        
        # Add discover button to context
        extra_context = extra_context or {}
        discover_url = request.path + '?action=discover'
        extra_context['discover_plugins_url'] = discover_url
        
        # Auto-discover plugins if none exist
        if not PluginManager.objects.exists():
            PluginManager.discover_plugins()
        
        return super().changelist_view(request, extra_context)
