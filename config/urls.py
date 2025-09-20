"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import dynamic admin configuration
from core.admin_config import update_admin_site
update_admin_site()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),           # Homepage
    path('products/', include('catalog.urls')), # Product catalog
    path('users/', include('users.urls')),    # User auth (if exists)
    path('orders/', include('orders.urls')),  # Order management
    path('wishlist/', include('wishlist.urls')), # Wishlist functionality
    path('updates/', include('updates.urls')), # Update management
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
