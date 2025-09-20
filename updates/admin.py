from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from .models import UpdateSettings, UpdateCheck, UpdateLog, AvailableUpdate, UpdateNotification


class UpdatesAdminSite(admin.AdminSite):
    """Custom admin site for updates management"""
    site_header = 'CMS Updates Management'
    site_title = 'Updates Admin'
    index_title = 'Update System Dashboard'

    def index(self, request, extra_context=None):
        """Redirect to updates dashboard"""
        return HttpResponseRedirect('/updates/')


# Create separate admin site instance for updates
updates_admin_site = UpdatesAdminSite(name='updates_admin')


@admin.register(UpdateSettings)
class UpdateSettingsAdmin(admin.ModelAdmin):
    """Admin interface for update settings"""

    def has_add_permission(self, request):
        # Only allow one settings instance
        return not UpdateSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False

    def changelist_view(self, request, extra_context=None):
        # Redirect to edit view if settings exist
        if UpdateSettings.objects.exists():
            settings = UpdateSettings.objects.first()
            return self.change_view(request, str(settings.pk))
        return super().changelist_view(request, extra_context)

    fieldsets = (
        ('Automatic Updates', {
            'fields': ('auto_check_enabled', 'check_frequency', 'auto_install_enabled', 'install_critical_updates'),
            'description': 'Configure automatic update checking and installation'
        }),
        ('Backup Settings', {
            'fields': ('backup_before_update', 'max_backups_to_keep'),
            'description': 'Backup configuration for updates'
        }),
        ('GitHub Integration', {
            'fields': ('update_server_url', 'api_key', 'beta_updates'),
            'description': 'GitHub releases integration - Leave update_server_url as default for GitHub'
        }),
        ('Notifications', {
            'fields': ('notification_email',),
            'description': 'Email notifications for updates'
        }),
    )


@admin.register(UpdateCheck)
class UpdateCheckAdmin(admin.ModelAdmin):
    """Admin interface for update checks"""

    list_display = ('check_date', 'current_version', 'latest_version', 'update_available', 'critical_update', 'check_successful')
    list_filter = ('check_successful', 'update_available', 'critical_update', 'check_date')
    search_fields = ('current_version', 'latest_version', 'error_message')
    readonly_fields = ('check_date',)

    def has_add_permission(self, request):
        return False  # Checks are created automatically

    def has_change_permission(self, request, obj=None):
        return False  # Read-only


@admin.register(UpdateLog)
class UpdateLogAdmin(admin.ModelAdmin):
    """Admin interface for update logs"""

    list_display = ('update_summary', 'status_display', 'started_at', 'initiated_by', 'auto_update')
    list_filter = ('status', 'auto_update', 'started_at')
    search_fields = ('from_version', 'to_version', 'error_message')
    readonly_fields = ('started_at', 'completed_at')

    def update_summary(self, obj):
        """Display update summary"""
        return f"{obj.from_version} → {obj.to_version}"
    update_summary.short_description = 'Update'

    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'completed': '#28a745',
            'failed': '#dc3545',
            'pending': '#ffc107',
            'downloading': '#17a2b8',
            'backing_up': '#6f42c1',
            'installing': '#fd7e14',
            'rolled_back': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def has_add_permission(self, request):
        return False  # Logs are created during updates


@admin.register(AvailableUpdate)
class AvailableUpdateAdmin(admin.ModelAdmin):
    """Admin interface for available updates"""

    list_display = ('version', 'critical_status', 'file_size_display', 'release_date', 'installed_status')
    list_filter = ('critical', 'beta', 'installed', 'release_date')
    search_fields = ('version', 'release_notes')
    readonly_fields = ('discovered_at',)

    def critical_status(self, obj):
        """Display critical status with icon"""
        if obj.critical:
            return format_html('<span style="color: #dc3545; font-weight: bold;">🔴 CRITICAL</span>')
        return format_html('<span style="color: #28a745;">🟢 Normal</span>')
    critical_status.short_description = 'Priority'

    def file_size_display(self, obj):
        """Display file size in human readable format"""
        return f"{obj.file_size_mb} MB"
    file_size_display.short_description = 'File Size'

    def installed_status(self, obj):
        """Display installation status"""
        if obj.installed:
            return format_html('<span style="color: #28a745;">✅ Installed</span>')
        return format_html('<span style="color: #ffc107;">⏳ Available</span>')
    installed_status.short_description = 'Status'


@admin.register(UpdateNotification)
class UpdateNotificationAdmin(admin.ModelAdmin):
    """Admin interface for update notifications"""

    list_display = ('title', 'notification_type_display', 'created_at', 'read_status', 'related_version')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('title', 'message', 'related_version')
    readonly_fields = ('created_at', 'read_at')

    def notification_type_display(self, obj):
        """Display notification type with color coding"""
        colors = {
            'update_available': '#17a2b8',
            'critical_update': '#dc3545',
            'update_completed': '#28a745',
            'update_failed': '#dc3545',
            'backup_created': '#6f42c1',
        }
        color = colors.get(obj.notification_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_display.short_description = 'Type'

    def read_status(self, obj):
        """Display read status with icon"""
        if obj.read:
            return format_html('<span style="color: #6c757d;">✅ Read</span>')
        return format_html('<span style="color: #ffc107; font-weight: bold;">📧 Unread</span>')
    read_status.short_description = 'Status'
