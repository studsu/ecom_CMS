from django.urls import path
from . import views

app_name = 'updates'

urlpatterns = [
    path('', views.update_dashboard, name='dashboard'),
    path('check/', views.check_updates, name='check_updates'),
    path('install/', views.install_update, name='install_update'),
    path('status/<int:update_log_id>/', views.update_status, name='update_status'),
    path('rollback/', views.rollback_update, name='rollback_update'),
    path('settings/', views.update_settings_view, name='settings'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('version-history/', views.version_history_view, name='version_history'),
]