from .manager import PluginManager

# Global plugin manager instance
plugin_manager = PluginManager()

__all__ = ['plugin_manager', 'PluginManager']