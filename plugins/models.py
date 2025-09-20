from django.db import models
from django.conf import settings
from catalog.models import Product
import json
from pathlib import Path

class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="plugin_reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="plugin_reviews"
    )
    rating = models.PositiveSmallIntegerField()  # 1..5
    title = models.CharField(max_length=200, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=True)  # can be moderated via admin
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_user_review_per_product",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.product} [{self.rating}]"


class PluginManager(models.Model):
    """Model to manage plugin activation/deactivation"""
    
    app_name = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50, default="1.0.0")
    is_active = models.BooleanField(default=True)
    plugin_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plugin"
        verbose_name_plural = "Plugin Management"
        ordering = ['name']
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({status})"
    
    @classmethod
    def discover_plugins(cls):
        """Discover all plugins in the plugins directory and create/update records"""
        from django.conf import settings
        
        plugins_dir = Path(settings.BASE_DIR) / "plugins"
        if not plugins_dir.exists():
            return
        
        discovered_apps = set()
        
        for child in plugins_dir.iterdir():
            if child.is_dir():
                meta_file = child / "plugin.json"
                if meta_file.exists():
                    try:
                        data = json.loads(meta_file.read_text())
                        app_name = data.get("app_name")
                        if app_name:
                            discovered_apps.add(app_name)
                            
                            # Create or update plugin record
                            plugin, created = cls.objects.get_or_create(
                                app_name=app_name,
                                defaults={
                                    'name': data.get('name', app_name),
                                    'description': data.get('description', ''),
                                    'version': data.get('version', '1.0.0'),
                                    'plugin_path': str(child),
                                    'is_active': True
                                }
                            )
                            
                            # Update existing plugin info
                            if not created:
                                plugin.name = data.get('name', app_name)
                                plugin.description = data.get('description', '')
                                plugin.version = data.get('version', '1.0.0')
                                plugin.plugin_path = str(child)
                                plugin.save()
                                
                    except Exception as e:
                        print(f"Error processing plugin {child}: {e}")
        
        # Mark plugins as inactive if they're no longer found
        cls.objects.exclude(app_name__in=discovered_apps).update(is_active=False)
    
    @classmethod
    def get_active_plugins(cls):
        """Get list of active plugin app names"""
        return list(cls.objects.filter(is_active=True).values_list('app_name', flat=True))
    
    def activate(self):
        """Activate the plugin"""
        self.is_active = True
        self.save()
    
    def deactivate(self):
        """Deactivate the plugin"""
        self.is_active = False
        self.save()
