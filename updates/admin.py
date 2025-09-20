from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import VersionCheck, UpdateSettings


@admin.register(UpdateSettings)
class UpdateSettingsAdmin(admin.ModelAdmin):
    """Admin for update settings"""
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not UpdateSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        # Redirect to edit view if settings exist
        if UpdateSettings.objects.exists():
            settings = UpdateSettings.objects.first()
            return HttpResponseRedirect(f'/admin/updates/updatesettings/{settings.pk}/change/')
        return super().changelist_view(request, extra_context)


@admin.register(VersionCheck)
class VersionCheckAdmin(admin.ModelAdmin):
    """Admin for version checks with check button"""
    
    list_display = ('check_date', 'current_version', 'latest_version', 'status_display', 'update_status')
    list_filter = ('check_successful', 'update_available', 'check_date')
    search_fields = ('current_version', 'latest_version', 'error_message')
    readonly_fields = ('check_date', 'current_version', 'latest_version', 'update_available', 'check_successful', 'error_message')
    change_list_template = 'admin/updates/versioncheck/change_list.html'
    
    def has_add_permission(self, request):
        return False  # Checks are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Read-only
    
    def status_display(self, obj):
        """Display check status with color coding"""
        if obj.check_successful:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ Success</span>')
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">❌ Failed</span>')
    status_display.short_description = 'Check Status'
    
    def update_status(self, obj):
        """Display update status with color coding"""
        if obj.update_available:
            return format_html('<span style="color: #007cba; font-weight: bold;">🆙 Update Available</span>')
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ Latest Version</span>')
    update_status.short_description = 'Update Status'
    
    def changelist_view(self, request, extra_context=None):
        """Add check updates button to the changelist"""
        # Handle check updates request
        if request.GET.get('check_updates'):
            from .git_checker import git_checker
            from .models import UpdateSettings
            
            # Get settings
            settings = UpdateSettings.get_settings()
            
            # Check for updates
            result = git_checker.check_for_updates(
                include_prereleases=settings.include_prereleases
            )
            
            # Log the check
            VersionCheck.objects.create(
                current_version=result['current_version'],
                latest_version=result.get('latest_version', ''),
                update_available=result.get('update_available', False),
                check_successful=result['success'],
                error_message=result.get('error', ''),
            )
            
            # Add message to show results
            from django.contrib import messages
            if result['success']:
                if result.get('update_available'):
                    messages.success(request, 
                        f"🆙 Update available: {result['latest_version']}! "
                        f"Current: {result['current_version']} "
                        f"{'(Pre-release)' if result.get('prerelease') else ''}")
                else:
                    messages.success(request, 
                        f"✅ You are running the latest version! Current: {result['current_version']}")
            else:
                messages.error(request, f"❌ Error checking updates: {result.get('error')}")
        
        # Add button and current version to extra context
        extra_context = extra_context or {}
        check_url = request.path + '?check_updates=1'
        extra_context['check_updates_url'] = check_url
        
        # Get current version to display
        from .git_checker import git_checker
        current_version = git_checker.get_current_version()
        extra_context['current_version'] = current_version
        
        return super().changelist_view(request, extra_context)


# Customize admin site
admin.site.site_header = 'CMS Updates Management'
admin.site.site_title = 'Updates Admin'
admin.site.index_title = 'Version Control & Updates'
