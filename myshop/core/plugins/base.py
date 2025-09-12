from abc import ABC, abstractmethod
from django.urls import path, include
from django.contrib import admin
from typing import List, Dict, Any, Optional


class PluginBase(ABC):
    """
    Base class for all plugins in the system.
    Each plugin must inherit from this class and implement required methods.
    """
    
    def __init__(self):
        self.name = self.get_name()
        self.version = self.get_version()
        self.description = self.get_description()
        self.author = self.get_author()
        self.enabled = True
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the plugin name"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return the plugin version"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return the plugin description"""
        pass
    
    @abstractmethod
    def get_author(self) -> str:
        """Return the plugin author"""
        pass
    
    def get_dependencies(self) -> List[str]:
        """Return list of required plugin dependencies"""
        return []
    
    def get_models(self) -> List[Any]:
        """Return list of Django models this plugin provides"""
        return []
    
    def get_admin_classes(self) -> List[tuple]:
        """Return list of (model, admin_class) tuples for Django admin"""
        return []
    
    def get_urls(self) -> List[Any]:
        """Return list of URL patterns this plugin provides"""
        return []
    
    def get_url_namespace(self) -> Optional[str]:
        """Return URL namespace for this plugin (optional)"""
        return None
    
    def get_templates_dir(self) -> Optional[str]:
        """Return path to plugin's template directory"""
        return None
    
    def get_static_dir(self) -> Optional[str]:
        """Return path to plugin's static files directory"""
        return None
    
    def get_context_processors(self) -> List[str]:
        """Return list of context processor paths"""
        return []
    
    def get_middleware(self) -> List[str]:
        """Return list of middleware classes"""
        return []
    
    def install(self):
        """Called when plugin is first installed"""
        pass
    
    def uninstall(self):
        """Called when plugin is uninstalled"""
        pass
    
    def activate(self):
        """Called when plugin is activated"""
        self.enabled = True
    
    def deactivate(self):
        """Called when plugin is deactivated"""
        self.enabled = False
    
    def on_ready(self):
        """Called when Django app is ready"""
        pass
    
    def get_settings(self) -> Dict[str, Any]:
        """Return plugin-specific settings"""
        return {}


class ModelPluginMixin:
    """
    Mixin for plugins that provide Django models
    """
    
    def register_models(self):
        """Register plugin models with Django"""
        from django.apps import apps
        
        for model in self.get_models():
            if not apps.get_model(model._meta.app_label, model._meta.object_name, require_ready=False):
                # Register model if not already registered
                pass


class AdminPluginMixin:
    """
    Mixin for plugins that provide Django admin interfaces
    """
    
    def register_admin(self):
        """Register plugin admin classes with Django admin"""
        for model, admin_class in self.get_admin_classes():
            if not admin.site.is_registered(model):
                admin.site.register(model, admin_class)


class URLPluginMixin:
    """
    Mixin for plugins that provide URL patterns
    """
    
    def get_url_patterns(self):
        """Return URL patterns for this plugin"""
        urls = self.get_urls()
        if not urls:
            return []
        
        namespace = self.get_url_namespace()
        if namespace:
            return [path(f'{self.name.lower()}/', include((urls, namespace)))]
        else:
            return [path(f'{self.name.lower()}/', include(urls))]


class TemplatePluginMixin:
    """
    Mixin for plugins that provide templates
    """
    
    def get_template_dirs(self):
        """Return template directories for this plugin"""
        template_dir = self.get_templates_dir()
        return [template_dir] if template_dir else []


class StaticPluginMixin:
    """
    Mixin for plugins that provide static files
    """
    
    def get_static_dirs(self):
        """Return static file directories for this plugin"""
        static_dir = self.get_static_dir()
        return [static_dir] if static_dir else []


class FullPlugin(PluginBase, ModelPluginMixin, AdminPluginMixin, URLPluginMixin, TemplatePluginMixin, StaticPluginMixin):
    """
    Full-featured plugin base class that includes all mixins
    """
    pass