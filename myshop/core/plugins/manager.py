import os
import importlib
import sys
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.apps import apps
from django.urls import path, include
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
import logging

from .base import PluginBase

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Central plugin management system
    """
    
    def __init__(self):
        self._plugins: Dict[str, PluginBase] = {}
        self._plugin_urls: List[Any] = []
        self._discovered = False
    
    def discover_and_load_plugins(self):
        """
        Discover and load all available plugins
        """
        if self._discovered:
            return
        
        plugin_dirs = self._get_plugin_directories()
        
        for plugin_dir in plugin_dirs:
            if os.path.exists(plugin_dir):
                self._discover_plugins_in_directory(plugin_dir)
        
        self._load_all_plugins()
        self._discovered = True
    
    def _get_plugin_directories(self) -> List[str]:
        """
        Get list of directories to search for plugins
        """
        base_dir = getattr(settings, 'BASE_DIR', os.getcwd())
        
        # Default plugin directories
        plugin_dirs = [
            os.path.join(base_dir, 'plugins'),
            os.path.join(base_dir, 'myshop', 'plugins'),
        ]
        
        # Add custom plugin directories from settings
        custom_dirs = getattr(settings, 'PLUGIN_DIRECTORIES', [])
        plugin_dirs.extend(custom_dirs)
        
        return plugin_dirs
    
    def _discover_plugins_in_directory(self, plugin_dir: str):
        """
        Discover plugins in a specific directory
        """
        if not os.path.exists(plugin_dir):
            return
        
        # Add plugin directory to Python path if not already there
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        
        # Scan for plugin packages
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)
            
            # Check if it's a directory with __init__.py (Python package)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, '__init__.py')):
                plugin_file = os.path.join(item_path, 'plugin.py')
                
                # Check if plugin.py exists
                if os.path.exists(plugin_file):
                    try:
                        self._load_plugin_from_file(item, item_path)
                    except Exception as e:
                        logger.error(f"Failed to load plugin {item}: {str(e)}")
    
    def _load_plugin_from_file(self, plugin_name: str, plugin_path: str):
        """
        Load a specific plugin from file
        """
        try:
            # Import the plugin module
            spec = importlib.util.spec_from_file_location(
                f"{plugin_name}.plugin", 
                os.path.join(plugin_path, 'plugin.py')
            )
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            
            # Look for plugin class (should inherit from PluginBase)
            plugin_class = None
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginBase) and 
                    attr != PluginBase):
                    plugin_class = attr
                    break
            
            if plugin_class:
                plugin_instance = plugin_class()
                self._register_plugin(plugin_instance)
                logger.info(f"Loaded plugin: {plugin_instance.name}")
            else:
                logger.warning(f"No valid plugin class found in {plugin_name}")
                
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
    
    def _load_all_plugins(self):
        """
        Initialize all loaded plugins
        """
        for plugin in self._plugins.values():
            try:
                if plugin.enabled:
                    self._initialize_plugin(plugin)
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin.name}: {str(e)}")
    
    def _register_plugin(self, plugin: PluginBase):
        """
        Register a plugin instance
        """
        self._plugins[plugin.name] = plugin
    
    def _initialize_plugin(self, plugin: PluginBase):
        """
        Initialize a single plugin
        """
        # Register models
        if hasattr(plugin, 'register_models'):
            plugin.register_models()
        
        # Register admin interfaces
        if hasattr(plugin, 'register_admin'):
            plugin.register_admin()
        
        # Collect URL patterns
        if hasattr(plugin, 'get_url_patterns'):
            plugin_urls = plugin.get_url_patterns()
            if plugin_urls:
                self._plugin_urls.extend(plugin_urls)
        
        # Call plugin's on_ready method
        plugin.on_ready()
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """
        Get a specific plugin by name
        """
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """
        Get all registered plugins
        """
        return self._plugins.copy()
    
    def get_enabled_plugins(self) -> Dict[str, PluginBase]:
        """
        Get all enabled plugins
        """
        return {name: plugin for name, plugin in self._plugins.items() if plugin.enabled}
    
    def enable_plugin(self, name: str) -> bool:
        """
        Enable a plugin
        """
        plugin = self._plugins.get(name)
        if plugin:
            plugin.activate()
            self._initialize_plugin(plugin)
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        Disable a plugin
        """
        plugin = self._plugins.get(name)
        if plugin:
            plugin.deactivate()
            return True
        return False
    
    def get_plugin_urls(self) -> List[Any]:
        """
        Get all plugin URL patterns
        """
        return self._plugin_urls
    
    def get_plugin_context_processors(self) -> List[str]:
        """
        Get all plugin context processors
        """
        processors = []
        for plugin in self.get_enabled_plugins().values():
            processors.extend(plugin.get_context_processors())
        return processors
    
    def get_plugin_middleware(self) -> List[str]:
        """
        Get all plugin middleware
        """
        middleware = []
        for plugin in self.get_enabled_plugins().values():
            middleware.extend(plugin.get_middleware())
        return middleware
    
    def get_plugin_template_dirs(self) -> List[str]:
        """
        Get all plugin template directories
        """
        template_dirs = []
        for plugin in self.get_enabled_plugins().values():
            if hasattr(plugin, 'get_template_dirs'):
                template_dirs.extend(plugin.get_template_dirs())
        return template_dirs
    
    def get_plugin_static_dirs(self) -> List[str]:
        """
        Get all plugin static file directories
        """
        static_dirs = []
        for plugin in self.get_enabled_plugins().values():
            if hasattr(plugin, 'get_static_dirs'):
                static_dirs.extend(plugin.get_static_dirs())
        return static_dirs