from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json


class UpdateSettings(models.Model):
    """Global update settings for the CMS"""

    CHECK_FREQUENCIES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('manual', 'Manual Only'),
    ]

    auto_check_enabled = models.BooleanField(
        default=True,
        help_text="Automatically check for updates"
    )
    auto_install_enabled = models.BooleanField(
        default=False,
        help_text="Automatically install non-critical updates"
    )
    check_frequency = models.CharField(
        max_length=20,
        choices=CHECK_FREQUENCIES,
        default='weekly',
        help_text="How often to check for updates"
    )
    install_critical_updates = models.BooleanField(
        default=True,
        help_text="Automatically install critical security updates"
    )
    backup_before_update = models.BooleanField(
        default=True,
        help_text="Create backup before applying updates"
    )
    max_backups_to_keep = models.PositiveIntegerField(
        default=5,
        help_text="Maximum number of backups to keep"
    )
    update_server_url = models.URLField(
        default="https://api.github.com/repos/studsu/ecom_CMS/releases",
        help_text="GitHub releases API URL (leave as default for automatic GitHub integration)"
    )
    api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="GitHub token for higher API rate limits (optional but recommended)"
    )
    notification_email = models.EmailField(
        blank=True,
        help_text="Email to notify about available updates"
    )
    beta_updates = models.BooleanField(
        default=False,
        help_text="Include beta/pre-release updates"
    )

    class Meta:
        verbose_name = "Update Settings"
        verbose_name_plural = "Update Settings"

    def __str__(self):
        return "Update Settings"

    @classmethod
    def get_settings(cls):
        """Get or create update settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        self.pk = 1
        super().save(*args, **kwargs)


class UpdateCheck(models.Model):
    """Record of update checks"""

    check_date = models.DateTimeField(auto_now_add=True)
    current_version = models.CharField(max_length=50)
    latest_version = models.CharField(max_length=50, blank=True)
    update_available = models.BooleanField(default=False)
    critical_update = models.BooleanField(default=False)
    check_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    response_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-check_date']
        verbose_name = "Update Check"
        verbose_name_plural = "Update Checks"

    def __str__(self):
        status = "Available" if self.update_available else "Up to date"
        return f"Update check {self.check_date.strftime('%Y-%m-%d %H:%M')} - {status}"


class UpdateLog(models.Model):
    """Log of update installations"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('downloading', 'Downloading'),
        ('backing_up', 'Creating Backup'),
        ('installing', 'Installing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    from_version = models.CharField(max_length=50)
    to_version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    initiated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who initiated the update"
    )
    auto_update = models.BooleanField(
        default=False,
        help_text="Whether this was an automatic update"
    )
    backup_path = models.CharField(max_length=500, blank=True)
    download_size = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    release_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = "Update Log"
        verbose_name_plural = "Update Logs"

    def __str__(self):
        return f"Update {self.from_version} → {self.to_version} ({self.status})"

    @property
    def duration(self):
        """Get update duration if completed"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return None

    def mark_completed(self):
        """Mark update as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error_message=""):
        """Mark update as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()


class AvailableUpdate(models.Model):
    """Available updates from update server"""

    version = models.CharField(max_length=50, unique=True)
    release_date = models.DateTimeField()
    download_url = models.URLField()
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    checksum = models.CharField(max_length=64)
    critical = models.BooleanField(default=False)
    beta = models.BooleanField(default=False)
    min_version_required = models.CharField(
        max_length=50,
        blank=True,
        help_text="Minimum version required for this update"
    )
    release_notes = models.TextField(blank=True)
    compatibility_notes = models.TextField(blank=True)
    discovered_at = models.DateTimeField(auto_now_add=True)
    installed = models.BooleanField(default=False)
    install_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-release_date']
        verbose_name = "Available Update"
        verbose_name_plural = "Available Updates"

    def __str__(self):
        return f"Version {self.version} ({'Critical' if self.critical else 'Normal'})"

    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class UpdateNotification(models.Model):
    """Notifications about updates"""

    NOTIFICATION_TYPES = [
        ('update_available', 'Update Available'),
        ('critical_update', 'Critical Update'),
        ('update_completed', 'Update Completed'),
        ('update_failed', 'Update Failed'),
        ('backup_created', 'Backup Created'),
    ]

    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    related_version = models.CharField(max_length=50, blank=True)
    action_url = models.URLField(blank=True)
    action_label = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Update Notification"
        verbose_name_plural = "Update Notifications"

    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title}"

    def mark_read(self):
        """Mark notification as read"""
        self.read = True
        self.read_at = timezone.now()
        self.save()
