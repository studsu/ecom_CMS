from django.db import models
from django.utils import timezone


class VersionCheck(models.Model):
    """Model to store version check results"""
    current_version = models.CharField(max_length=100)
    latest_version = models.CharField(max_length=100, blank=True)
    update_available = models.BooleanField(default=False)
    check_date = models.DateTimeField(default=timezone.now)
    check_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-check_date']
        verbose_name = 'Version Check'
        verbose_name_plural = 'Version Checks'
    
    def __str__(self):
        status = "Success" if self.check_successful else "Failed"
        update_status = "Update Available" if self.update_available else "Latest"
        return f"{self.check_date.strftime('%Y-%m-%d %H:%M')} - {self.current_version} - {update_status} - {status}"


class UpdateSettings(models.Model):
    """Singleton model for update settings"""
    auto_check_enabled = models.BooleanField(default=True, help_text="Automatically check for updates")
    check_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='weekly'
    )
    include_prereleases = models.BooleanField(default=False, help_text="Include pre-release versions")
    
    class Meta:
        verbose_name = 'Update Settings'
        verbose_name_plural = 'Update Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and UpdateSettings.objects.exists():
            # Update existing instance instead of creating new one
            existing = UpdateSettings.objects.first()
            existing.auto_check_enabled = self.auto_check_enabled
            existing.check_frequency = self.check_frequency
            existing.include_prereleases = self.include_prereleases
            existing.save()
            return existing
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'auto_check_enabled': True,
                'check_frequency': 'weekly',
                'include_prereleases': False,
            }
        )
        return settings
    
    def __str__(self):
        return f"Update Settings - Auto: {self.auto_check_enabled} - Frequency: {self.check_frequency}"
