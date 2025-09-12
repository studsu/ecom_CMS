from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("users/", include("users.urls")),
    path("products/", include("catalog.urls")),
    path("orders/", include("orders.urls")),
]
